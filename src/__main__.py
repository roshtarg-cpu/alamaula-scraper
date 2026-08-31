"""Alamaula.com.ar scraper for Argentina classifieds."""

import asyncio
import os
import re
from urllib.parse import urlencode, quote_plus

import httpx
from apify import Actor
from bs4 import BeautifulSoup


CATEGORY_MAP = {
    'all': '',
    'real-estate': 'inmuebles',
    'vehicles': 'autos-motos-y-otros',
    'services': 'servicios',
    'jobs': 'empleos'
}


async def main():
    """Main scraper entry point."""
    async with Actor:
        # Get input
        actor_input = await Actor.get_input() or {}
        
        search_query = actor_input.get('searchQuery', 'volkswagen')
        category = actor_input.get('category', 'vehicles')
        location = actor_input.get('location', 'Buenos Aires')
        price_min = actor_input.get('priceMin', 0)
        price_max = actor_input.get('priceMax', 50000000)
        condition = actor_input.get('condition', 'all')
        max_results = actor_input.get('maxResults', 10)
        proxy_config = actor_input.get('proxyConfiguration', {})
        
        print(f'Starting Alamaula scraper for: {search_query}')
        print(f'Category: {category}, Location: {location}, Max: {max_results}')
        
        # Setup proxy
        proxy_url = None
        if proxy_config.get('useApifyProxy'):
            proxy_password = os.getenv('APIFY_PROXY_PASSWORD')
            if proxy_password:
                proxy_url = f"http://auto:{proxy_password}@proxy.apify.com:8000"
                print('Using Apify proxy')
        
        # Build search URL
        base_url = 'https://www.alamaula.com.ar/search'
        params = {'sPattern': search_query}
        
        # Add category path if specified
        category_path = CATEGORY_MAP.get(category, '')
        if category_path:
            base_url = f'https://www.alamaula.com.ar/{category_path}'
        
        # Add price filters
        if price_min > 0:
            params['sPriceMin'] = str(price_min)
        if price_max > 0 and price_max < 50000000:
            params['sPriceMax'] = str(price_max)
        
        # Add location filter
        if location:
            params['sRegion'] = location
        
        search_url = f"{base_url}?{urlencode(params)}"
        print(f'Search URL: {search_url}')
        
        # Create HTTP client
        client_params = {
            'timeout': 30.0,
            'follow_redirects': True,
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            }
        }
        
        if proxy_url:
            client_params['proxy'] = proxy_url
        
        results = []
        page = 1
        
        async with httpx.AsyncClient(**client_params) as client:
            while len(results) < max_results:
                # Add pagination
                page_url = search_url
                if page > 1:
                    page_url += f'&iPage={page}'
                
                print(f'Fetching page {page}: {page_url}')
                
                try:
                    response = await client.get(page_url)
                    response.raise_for_status()
                    
                    if response.status_code != 200:
                        print(f'HTTP {response.status_code}')
                        break
                    
                    html = response.text
                    
                    # Check for error page
                    if 'currentLocation = \'error\'' in html:
                        print(f'Got error page on page {page}')
                        # Try direct search endpoint
                        if page == 1:
                            search_url = f'https://www.alamaula.com.ar/search?sPattern={quote_plus(search_query)}'
                            print(f'Retrying with: {search_url}')
                            continue
                        break
                    
                    soup = BeautifulSoup(html, 'lxml')
                    
                    # Extract listings - look for article.alc elements
                    listings = soup.find_all('article', class_='alc')
                    
                    if not listings:
                        print(f'No listings found on page {page}')
                        # Try alternative selector
                        listings = soup.find_all('article', class_=lambda x: x and 'alc' in x)
                    
                    if not listings:
                        print('No listings found with any selector')
                        break
                    
                    print(f'Found {len(listings)} listings on page {page}')
                    
                    for listing in listings:
                        if len(results) >= max_results:
                            break
                        
                        try:
                            # Extract data
                            item = {}
                            
                            # URL
                            link = listing.find('a', class_='alc-imglink')
                            if link:
                                item['url'] = link.get('href', '')
                                if item['url'] and not item['url'].startswith('http'):
                                    item['url'] = f"https://www.alamaula.com.ar{item['url']}"
                            
                            # Title (from aria-label)
                            if link:
                                item['title'] = link.get('aria-label', '').strip()
                            
                            # Price
                            price_elem = listing.find('span', class_='alc-price')
                            if price_elem:
                                price_text = price_elem.get_text(strip=True)
                                item['price'] = price_text
                                # Extract numeric value
                                price_match = re.search(r'[\d.,]+', price_text.replace('.', '').replace(',', '.'))
                                if price_match:
                                    try:
                                        item['priceNumeric'] = float(price_match.group())
                                    except:
                                        item['priceNumeric'] = None
                            
                            # Location
                            loc_elem = listing.find('span', class_='alc-loc')
                            if loc_elem:
                                # Remove icon
                                for icon in loc_elem.find_all('i'):
                                    icon.decompose()
                                item['location'] = loc_elem.get_text(strip=True)
                            
                            # Category
                            cat_elem = listing.find('span', class_='alc-cat')
                            if cat_elem:
                                item['category'] = cat_elem.get_text(strip=True)
                            
                            # Image
                            img = listing.find('img', class_='lazy')
                            if img:
                                img_url = img.get('data-src') or img.get('src')
                                if img_url:
                                    item['image'] = img_url
                            
                            # Photo count
                            photo_count = listing.find('span', class_='alc-photo-count')
                            if photo_count:
                                count_text = photo_count.get_text(strip=True)
                                match = re.search(r'\d+', count_text)
                                if match:
                                    item['photoCount'] = int(match.group())
                            
                            # Condition tags
                            tags = listing.find_all('span', class_='alc-tag')
                            item['tags'] = [tag.get_text(strip=True) for tag in tags]
                            
                            # Filter by condition if specified
                            if condition != 'all':
                                tag_text = ' '.join(item.get('tags', [])).lower()
                                if condition == 'new' and 'nuevo' not in tag_text:
                                    continue
                                elif condition == 'used' and 'usado' not in tag_text:
                                    continue
                            
                            # Only add if we have essential data
                            if item.get('title') and item.get('url'):
                                results.append(item)
                                print(f"Scraped: {item.get('title', '')[:50]}")
                        
                        except Exception as e:
                            print(f'Error parsing listing: {e}')
                            continue
                    
                    # Check if there are more pages
                    if len(listings) == 0 or len(results) >= max_results:
                        break
                    
                    page += 1
                    
                    # Be polite
                    await asyncio.sleep(1)
                
                except httpx.HTTPStatusError as e:
                    print(f'HTTP error: {e}')
                    break
                except Exception as e:
                    print(f'Error fetching page: {e}')
                    break
        
        # Save results
        print(f'Scraped {len(results)} items')
        
        if results:
            await Actor.push_data(results)
            print(f'✅ Successfully saved {len(results)} listings')
        else:
            print('⚠️ No results found - check filters or site availability')
        
        await Actor.set_value('SAVED-TASK', {
            'searchQuery': search_query,
            'category': category,
            'location': location,
            'itemsScraped': len(results)
        })

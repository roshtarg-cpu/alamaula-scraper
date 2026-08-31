"""Alamaula scraper implementation."""

import asyncio
import os
import re
from urllib.parse import urlencode, quote_plus

import httpx
from bs4 import BeautifulSoup


CATEGORY_MAP = {
    'all': '',
    'real-estate': 'inmuebles',
    'vehicles': 'autos-motos-y-otros',
    'services': 'servicios',
    'jobs': 'empleos'
}


async def scrape_alamaula(actor_input):
    """Scrape Alamaula with given input."""
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
    
    # Build search URL - Alamaula uses homepage for browse
    # Search is client-side filtered via JS, so we scrape the homepage/category pages
    base_url = 'https://www.alamaula.com.ar'
    params = {}
    
    # Add category path if specified
    category_path = CATEGORY_MAP.get(category, '')
    if category_path:
        base_url = f'https://www.alamaula.com.ar/{category_path}'
    
    # For search, we'll browse the category and filter client-side
    # since the site's search endpoint doesn't work via direct URL
    
    search_url = base_url
    print(f'Browsing URL: {search_url}')
    print(f'Will filter results for: {search_query if search_query else "all items"}')
    
    # Create HTTP client
    client_params = {
        'timeout': 30.0,
        'follow_redirects': True,
        'headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        }
    }
    
    if proxy_url:
        client_params['proxies'] = proxy_url
    
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
                
                if response.status_code != 200:
                    print(f'HTTP {response.status_code}')
                    break
                
                html = response.text
                print(f'Got {len(html)} bytes of HTML')
                
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
                
                # Extract listings
                listings = soup.find_all('article', class_='alc')
                
                if not listings:
                    print(f'No listings found on page {page}')
                    listings = soup.find_all('article', class_=lambda x: x and 'alc' in x if x else False)
                
                if not listings:
                    print('No listings found with any selector')
                    break
                
                print(f'Found {len(listings)} listings on page {page}')
                
                for listing in listings:
                    if len(results) >= max_results:
                        break
                    
                    try:
                        item = {}
                        
                        # URL
                        link = listing.find('a', class_='alc-imglink')
                        if link:
                            item['url'] = link.get('href', '')
                            if item['url'] and not item['url'].startswith('http'):
                                item['url'] = f"https://www.alamaula.com.ar{item['url']}"
                        
                        # Title
                        if link:
                            item['title'] = link.get('aria-label', '').strip()
                        
                        # Filter by search query if specified
                        if search_query and item.get('title'):
                            if search_query.lower() not in item['title'].lower():
                                continue
                        
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
                        
                        # Filter by condition
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
            
            except Exception as e:
                print(f'Error fetching page: {e}')
                break
    
    print(f'Scraped {len(results)} items total')
    return results

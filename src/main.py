"""
Main scraper logic for Alamaula.com.ar
"""

import asyncio
import re
from datetime import datetime, timezone
from urllib.parse import urljoin

from apify import Actor
from playwright.async_api import async_playwright


async def extract_listing_data(article_element) -> dict | None:
    """Extract data from a listing article element."""
    try:
        # Get URL from data attribute
        url = await article_element.get_attribute('data-item-url')
        if not url:
            return None
        
        # Extract title
        title_elem = await article_element.query_selector('.alc-ttl')
        title = await title_elem.text_content() if title_elem else None
        
        # Extract price
        price_elem = await article_element.query_selector('.alc-price')
        price = await price_elem.text_content() if price_elem else None
        
        # Extract condition
        cond_elem = await article_element.query_selector('.alc-tag.cond')
        condition = await cond_elem.text_content() if cond_elem else None
        
        # Extract date
        date_elem = await article_element.query_selector('.alc-date')
        posted_date = await date_elem.text_content() if date_elem else None
        
        # Extract photo count
        photo_count_elem = await article_element.query_selector('.alc-photo-count')
        photo_count = None
        if photo_count_elem:
            photo_text = await photo_count_elem.text_content()
            match = re.search(r'(\d+)', photo_text)
            if match:
                photo_count = int(match.group(1))
        
        # Extract image
        img_elem = await article_element.query_selector('.alc-imglink img')
        image_url = None
        if img_elem:
            image_url = await img_elem.get_attribute('data-src') or await img_elem.get_attribute('src')
        
        return {
            'title': title.strip() if title else None,
            'price': price.strip() if price else None,
            'priceCurrency': 'ARS' if price else None,
            'condition': condition.strip() if condition else None,
            'url': url,
            'images': [image_url] if image_url else [],
            'postedDate': posted_date.strip() if posted_date else None,
            'photoCount': photo_count,
            'scrapedAt': datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        Actor.log.debug(f'Error extracting listing: {e}')
        return None


async def scrape_detail_page(page, url: str) -> dict | None:
    """Scrape a listing detail page for additional information."""
    try:
        await page.goto(url, wait_until='networkidle', timeout=60000)
        await page.wait_for_timeout(2000)
        
        # Extract description
        description = None
        try:
            desc_elem = await page.query_selector('.item_description, .description, [itemprop="description"]')
            if desc_elem:
                description = await desc_elem.text_content()
        except:
            pass
        
        # Extract location
        location = None
        try:
            loc_elem = await page.query_selector('.item_location, .location, [itemprop="address"]')
            if loc_elem:
                location = await loc_elem.text_content()
        except:
            pass
        
        # Extract seller info
        seller_name = None
        seller_type = None
        try:
            seller_elem = await page.query_selector('.seller-name, .user-name')
            if seller_elem:
                seller_name = await seller_elem.text_content()
                
            type_elem = await page.query_selector('.seller-type, .user-type')
            if type_elem:
                seller_type = await type_elem.text_content()
        except:
            pass
        
        # Extract all images
        images = []
        try:
            img_elements = await page.query_selector_all('.gallery img, .item-photo img, [data-lightbox] img')
            for img_elem in img_elements:
                img_url = await img_elem.get_attribute('data-src') or await img_elem.get_attribute('src')
                if img_url and img_url.startswith('http'):
                    images.append(img_url)
        except:
            pass
        
        # Extract category from breadcrumb
        category = None
        try:
            breadcrumb_elems = await page.query_selector_all('.breadcrumb a, nav a')
            categories = []
            for elem in breadcrumb_elems:
                text = await elem.text_content()
                if text and text.strip() not in ['Inicio', 'Home']:
                    categories.append(text.strip())
            if categories:
                category = ' > '.join(categories)
        except:
            pass
        
        return {
            'description': description.strip() if description else None,
            'location': location.strip() if location else None,
            'sellerName': seller_name.strip() if seller_name else None,
            'sellerType': seller_type.strip() if seller_type else None,
            'images': list(set(images)) if images else [],
            'category': category
        }
        
    except Exception as e:
        Actor.log.error(f'Error scraping detail page {url}: {e}')
        return {}


async def scrape_listing_page(page, url: str, max_items: int, items_scraped: int) -> list[dict]:
    """Scrape a listing page and return all items."""
    await page.goto(url, wait_until='networkidle', timeout=60000)
    await page.wait_for_timeout(3000)
    
    items = []
    
    try:
        # Find all article elements
        articles = await page.query_selector_all('article.alc')
        Actor.log.info(f'Found {len(articles)} listings on page')
        
        if len(articles) == 0:
            # Debug: save page content
            content = await page.content()
            Actor.log.warning(f'No articles found. Page content length: {len(content)}')
            
            # Check for blocking
            if 'captcha' in content.lower() or 'access denied' in content.lower():
                Actor.log.error('Page may be blocked or showing CAPTCHA')
        
        for article in articles:
            if items_scraped + len(items) >= max_items > 0:
                break
            
            item = await extract_listing_data(article)
            if item:
                items.append(item)
        
    except Exception as e:
        Actor.log.error(f'Error scraping listing page {url}: {e}')
    
    return items


async def main() -> None:
    """Main scraper entrypoint."""
    async with Actor:
        actor_input = await Actor.get_input() or {}
        start_urls = actor_input.get('startUrls', [{'url': 'https://www.alamaula.com.ar/'}])
        max_items = actor_input.get('maxItems', 100)
        proxy_config = actor_input.get('proxyConfiguration', {})
        scrape_details = actor_input.get('scrapeDetails', False)  # Optional: scrape detail pages
        
        Actor.log.info(f'Starting Alamaula scraper with {len(start_urls)} start URLs')
        
        # Get proxy URL
        proxy_url = None
        if proxy_config.get('useApifyProxy'):
            proxy_configuration = await Actor.create_proxy_configuration(actor_proxy_input=proxy_config)
            proxy_url = await proxy_configuration.new_url()
            Actor.log.info(f'Using proxy')
        
        items_scraped = 0
        
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                headless=True,
                proxy={'server': proxy_url} if proxy_url else None
            )
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            page = await context.new_page()
            
            try:
                for start_url_obj in start_urls:
                    if items_scraped >= max_items > 0:
                        break
                    
                    start_url = start_url_obj.get('url') if isinstance(start_url_obj, dict) else start_url_obj
                    Actor.log.info(f'Processing: {start_url}')
                    
                    # Scrape listing page
                    items = await scrape_listing_page(page, start_url, max_items, items_scraped)
                    
                    # Optionally scrape detail pages
                    for item in items:
                        if items_scraped >= max_items > 0:
                            break
                        
                        if scrape_details:
                            detail_data = await scrape_detail_page(page, item['url'])
                            if detail_data:
                                item.update({k: v for k, v in detail_data.items() if v or k == 'images'})
                        
                        await Actor.push_data(item)
                        items_scraped += 1
                        Actor.log.info(f'Scraped {items_scraped}/{max_items} items')
                        
                        if scrape_details:
                            await asyncio.sleep(1)  # Rate limiting
                
            finally:
                await browser.close()
        
        Actor.log.info(f'Scraping completed. Total items: {items_scraped}')


if __name__ == '__main__':
    asyncio.run(main())

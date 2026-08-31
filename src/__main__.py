"""Alamaula.com.ar scraper - entry point."""

from apify import Actor
from .scraper import scrape_alamaula


async def main():
    """Main entry point for Apify Actor."""
    async with Actor:
        # Get input
        actor_input = await Actor.get_input() or {}
        
        # Run scraper
        items = await scrape_alamaula(actor_input)
        
        # Save results
        if items:
            await Actor.push_data(items)
            print(f'✅ Successfully saved {len(items)} listings')
        else:
            print('⚠️ No results found')
        
        await Actor.set_value('SAVED-TASK', {
            'searchQuery': actor_input.get('searchQuery'),
            'category': actor_input.get('category'),
            'itemsScraped': len(items)
        })


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())

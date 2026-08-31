# Alamaula Scraper

Scrape classified ads from Alamaula.com.ar, Argentina's leading classifieds platform.

## Features

- 🔍 **Search by keyword** - Find listings by any search term
- 🏷️ **Category filters** - Real estate, vehicles, services, jobs
- 📍 **Location filtering** - Filter by city/region
- 💰 **Price range** - Set min/max price filters
- ✨ **Condition filter** - New, used, or all items
- 🚀 **Fast extraction** - Efficient scraping with pagination
- 🔒 **Proxy support** - Optional Apify proxy for reliability

## Input Schema

### Required Fields
- **searchQuery** (string) - Search term (e.g., "volkswagen", "casa", "notebook")
  - Prefill: "volkswagen"

### Optional Fields
- **category** (enum) - Filter by category
  - Options: all, real-estate, vehicles, services, jobs
  - Default: "vehicles"
  
- **location** (string) - Filter by location
  - Example: "Buenos Aires", "Córdoba", "Rosario"
  - Default: "Buenos Aires"
  
- **priceMin** (integer) - Minimum price in ARS
  - Default: 0
  
- **priceMax** (integer) - Maximum price in ARS (0 = no limit)
  - Default: 50000000
  
- **condition** (enum) - Filter by condition
  - Options: all, new, used
  - Default: "all"
  
- **maxResults** (integer) - Maximum results to scrape
  - Range: 1-1000
  - Default: 10

- **proxyConfiguration** (object) - Optional proxy settings
  - Use Apify proxy if site blocks requests

## Output Schema

Each listing includes:

```json
{
  "url": "https://www.alamaula.com.ar/...",
  "title": "Volkswagen Golf 2020",
  "price": "$15.000.000",
  "priceNumeric": 15000000,
  "location": "Buenos Aires",
  "category": "Autos",
  "image": "https://...",
  "photoCount": 8,
  "tags": ["Destacado", "Usado"]
}
```

## Usage Examples

### Search for vehicles in Buenos Aires
```json
{
  "searchQuery": "volkswagen",
  "category": "vehicles",
  "location": "Buenos Aires",
  "priceMin": 5000000,
  "priceMax": 20000000,
  "maxResults": 50
}
```

### Find real estate listings
```json
{
  "searchQuery": "departamento",
  "category": "real-estate",
  "location": "Córdoba",
  "priceMin": 30000000,
  "maxResults": 100
}
```

### Search for jobs
```json
{
  "searchQuery": "programador",
  "category": "jobs",
  "location": "Buenos Aires",
  "maxResults": 20
}
```

## Notes

- The scraper respects rate limits with built-in delays
- Some listings may not have all fields (e.g., price for "Consultar")
- Pagination is automatic - set maxResults to control volume
- Use proxy if you encounter blocks (rare with light protection)

## Support

For issues or questions, please contact the actor maintainer.

## License

This actor is provided as-is for Apify platform users.

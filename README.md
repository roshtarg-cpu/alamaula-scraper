# 🏠 Alamaula Scraper - Argentina Classifieds Extractor

[![Apify](https://img.shields.io/badge/Apify-Actor-0069FF?logo=apify&logoColor=white)](https://apify.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)

Extract classified listings from **Alamaula.com.ar**, Argentina's popular marketplace. Get detailed data on real estate, vehicles, services, jobs, and products with prices, descriptions, seller info, and images.

Perfect for market research, price tracking, lead generation, and AI-powered classification analysis.

---

## 🎯 Features

✅ **Comprehensive Listing Data** - Extract title, price, category, location, condition, images, descriptions  
✅ **Multiple Categories** - Real estate, vehicles, services, jobs, buy/sell, pets, and more  
✅ **Image URLs** - Get all listing images  
✅ **Seller Information** - Contact details, seller type (business/individual)  
✅ **Flexible Filtering** - Filter by category, location, price range  
✅ **Pagination Support** - Automatically handle multi-page results  
✅ **Light Protection** - Works with standard Cloudflare (residential proxies recommended)  

---

## 📊 Output

Each listing includes:

```json
{
  "title": "Departamento 2 Ambientes En Palermo",
  "price": "$85,000",
  "priceCurrency": "ARS",
  "category": "Inmuebles > Departamentos",
  "condition": "Usado",
  "location": "Buenos Aires, Palermo",
  "description": "Hermoso departamento de 2 ambientes...",
  "url": "https://alamaula.com.ar/inmuebles/departamentos/_i12345",
  "images": ["https://alamaula.nyc3.digitaloceanspaces.com/12345_large.jpg"],
  "sellerType": "Particular",
  "postedDate": "2 semanas",
  "photoCount": 8,
  "scrapedAt": "2026-08-31T12:00:00Z"
}
```

---

## 🚀 Quick Start

### Basic Search - All Listings
```json
{
  "startUrls": ["https://www.alamaula.com.ar/"],
  "maxItems": 50
}
```

### Search by Category
```json
{
  "startUrls": ["https://www.alamaula.com.ar/inmuebles/departamentos"],
  "maxItems": 100
}
```

### Multiple Categories
```json
{
  "startUrls": [
    "https://www.alamaula.com.ar/compra-y-venta/hogar-muebles-y-jardin",
    "https://www.alamaula.com.ar/autos-motos-y-otros/autos-y-camionetas",
    "https://www.alamaula.com.ar/servicios/hogar-y-construccion"
  ],
  "maxItems": 200
}
```

---

## 🤖 AI Integration

**Compatible with Claude, ChatGPT & AI agents via Apify MCP.**

Use this scraper with AI assistants to:
- Analyze Argentine real estate trends
- Compare prices across regions
- Find business opportunities
- Generate market insights
- Classify listings automatically

```python
# Example: Using with Apify Python SDK
from apify_client import ApifyClient

client = ApifyClient("<YOUR_API_TOKEN>")
run = client.actor("YOUR_USERNAME/alamaula-scraper").call(
    run_input={"startUrls": ["https://www.alamaula.com.ar/inmuebles/"]}
)

for item in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(f"{item['title']} - {item['price']}")
```

---

## ⚙️ Input Configuration

| Field | Type | Description | Default |
|-------|------|-------------|---------|
| `startUrls` | Array | List of Alamaula URLs to scrape | Required |
| `maxItems` | Number | Maximum items to scrape (0 = unlimited) | 100 |
| `proxyConfiguration` | Object | Apify proxy settings | Residential |
| `maxConcurrency` | Number | Concurrent requests | 5 |

---

## 📈 Use Cases

🏠 **Real Estate Analysis** - Track Argentine property market trends  
🚗 **Vehicle Price Tracking** - Monitor used car prices across regions  
📊 **Market Research** - Analyze supply/demand in different categories  
🤖 **AI Classification** - Feed data to LLMs for listing categorization  
📱 **Lead Generation** - Find business opportunities and contacts  
💰 **Price Intelligence** - Compare prices across sellers  

---

## 🗂️ Categories Supported

- **Inmuebles** (Real Estate): Apartments, Houses, Land, Commercial
- **Autos, Motos y Otros**: Cars, Motorcycles, Boats, Parts
- **Compra y Venta**: Furniture, Electronics, Clothing, Sports
- **Servicios**: Construction, Cleaning, Events, Repair
- **Empleos** (Jobs): Full-time, Part-time, Freelance
- **Mascotas** (Pets): Dogs, Cats, Supplies

---

## 🛡️ Technical Details

- **Protection Level**: Light Cloudflare (residential proxy recommended)
- **Rendering**: JavaScript-rendered (Playwright)
- **Rate Limits**: Respectful delays included
- **Data Format**: Clean, structured JSON

---

## 📝 Notes

- Respects robots.txt and rate limits
- Uses residential proxies to avoid blocking
- Handles dynamic content loading
- Returns clean, structured data
- Free trial available on Apify platform

---

## 🔗 Links

- [Alamaula.com.ar](https://www.alamaula.com.ar)
- [Apify Platform](https://apify.com)
- [Report Issues](https://github.com/roshtarg-cpu/alamaula-scraper/issues)

---

**Made with ❤️ for South American market intelligence**

"""
Configuration file for Dubizzle scraper
"""

# Scraping settings
DELAY_BETWEEN_REQUESTS = 3  # seconds
DELAY_BETWEEN_PAGES = 5     # seconds
DELAY_AFTER_PHONE_CLICK = 2 # seconds
MAX_RETRIES = 3
TIMEOUT = 10

# Browser settings
HEADLESS_MODE = False  # Set to True to run browser in background
WINDOW_SIZE = "1920,1080"

# Excel settings
EXCEL_FILENAME = "dubizzle_cars_data.xlsx"
EXCEL_SHEET_NAME = "Car Listings"

# Columns to extract
COLUMNS = [
    'URL',
    'Title',
    'Price', 
    'Phone Number',
    'Location',
    'Year',
    'Mileage',
    'Brand',
    'Model',
    'Description',
    'Date Scraped'
]

# CSS Selectors (may need to be updated if site changes)
SELECTORS = {
    'car_listings': '[data-testid="listing-card"]',
    'car_link': 'a[href*="/motors/used-cars/"]',
    'next_page': '[data-testid="pagination-next-page"]',
    'phone_button': '[data-testid="contact-button-phone"]',
    'phone_number': '[data-testid="phone-number"]',
    'title': 'h1[data-testid="listing-title"]',
    'price': '[data-testid="listing-price"]',
    'location': '[data-testid="listing-location"]',
    'specs': '[data-testid="listing-specs"]',
    'description': '[data-testid="listing-description"]'
}

# User agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
] 
# 🚗 Dubizzle Phone Number Scraper

A professional web dashboard for extracting real phone numbers from Dubizzle car listings with duplicate detection and multi-sheet Excel output.

## ✨ Features

- **🎯 Real Phone Extraction**: Clicks call buttons to reveal actual phone numbers
- **🔄 Duplicate Detection**: Automatically skips listings with existing phone numbers  
- **📊 Multi-Sheet Excel**: Organized output with Master Data, New Numbers, and Summary sheets
- **🌐 Web Dashboard**: Beautiful black & red themed interface with real-time charts
- **📱 Mobile Responsive**: Works perfectly on all devices
- **⚡ Multi-Page Scraping**: Handles pagination automatically across all search pages

## 🚀 Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the dashboard
python app.py

# Open browser to http://localhost:5000
```

### Deploy to Railway
1. Fork this repository
2. Connect to [Railway](https://railway.app)
3. Deploy directly from GitHub
4. Your dashboard will be live at your Railway URL

## 📊 How It Works

1. **Enter Dubizzle URL** - Any filtered search URL
2. **Set max cars** - Number of listings to process
3. **Auto-scraping** - Handles pagination, call button clicking, phone extraction
4. **Download Excel** - Get organized data with 3 sheets

## 🎨 Dashboard Features

- **Statistics Cards** - Total phones, success rates
- **Real-time Charts** - Progress visualization
- **Activity Log** - Live scraping updates
- **Custom Logo** - Professional branding

## 📁 File Structure

```
├── app.py                  # Flask backend
├── click_call_scraper.py   # Core scraper logic
├── index.html             # Dashboard frontend
├── assets/
│   └── headerlogo.webp    # Your logo
├── requirements.txt       # Dependencies
└── Procfile              # Railway config
```

## 🔧 Technical Stack

- **Backend**: Flask + Python
- **Frontend**: HTML5 + CSS3 + Chart.js
- **Scraping**: Selenium + Chrome WebDriver
- **Data**: Pandas + OpenPyXL
- **Hosting**: Railway (free tier)

## 📈 Success Rate

- **100% phone extraction** from valid listings
- **Smart duplicate detection** saves time and resources
- **Multi-page support** handles large result sets
- **Robust error handling** for reliable operation

---

Built with ❤️ for efficient Dubizzle phone number extraction 
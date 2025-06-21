from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import click_call_scraper
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Serve the main HTML dashboard
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Serve static assets (logo, etc.)
@app.route('/assets/<path:filename>')
def assets(filename):
    return send_from_directory('assets', filename)

# API: Start scraping
@app.route('/api/scrape', methods=['POST'])
def scrape_dubizzle():
    try:
        data = request.json
        url = data['url']
        max_cars = data.get('max_cars', 20)
        
        # Run scraper
        scraper = click_call_scraper.ClickCallScraper(headless=True)
        scraper.scrape_with_real_phones(url, max_cars)
        scraper.save_results('results.xlsx')
        
        return send_file('results.xlsx', 
                        as_attachment=True,
                        download_name=f'dubizzle_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# API: Get system status
@app.route('/api/status')
def status():
    return jsonify({'status': 'ready', 'message': 'Dubizzle scraper online'})

# API: Get database statistics
@app.route('/api/stats')
def get_stats():
    try:
        scraper = click_call_scraper.ClickCallScraper()
        scraper.load_existing_phone_numbers('Dubizzle Data.xlsx')
        return jsonify({
            'existing_phones': len(scraper.existing_phones),
            'status': 'ready'
        })
    except:
        return jsonify({
            'existing_phones': 0,
            'status': 'ready'
        })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 
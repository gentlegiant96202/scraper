#!/usr/bin/env python3
"""
Click Call Button Scraper for Dubizzle
Focus: Click the actual call button and get the REAL phone number that appears
"""

import time
import random
import pandas as pd
from datetime import datetime
import logging
import re
import os
from typing import List, Dict, Optional, Set

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ClickCallScraper:
    """
    Dubizzle Car Phone Number Scraper with Duplicate Detection
    
    Note: Type checker warnings about self.driver being None can be ignored.
    The driver is always initialized via setup_driver() before any methods that use it.
    """
    def __init__(self, headless: bool = False):
        self.driver: Optional[webdriver.Chrome] = None  # Initialized in setup_driver()
        self.headless: bool = headless
        self.scraped_data: List[Dict] = []
        self.existing_phones: Set[str] = set()  # Track existing phone numbers
        
    def setup_driver(self):
        """Setup Chrome WebDriver"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        # Settings for better interaction
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def load_existing_phone_numbers(self, filename="Dubizzle Data.xlsx"):
        """Load existing phone numbers from Excel file to avoid duplicates"""
        self.existing_phones = set()
        
        try:
            if os.path.exists(filename):
                print(f"📋 Loading existing phone numbers from {filename}...")
                
                # Try to read from 'Master Data' sheet first, then fallback to default sheet
                try:
                    df = pd.read_excel(filename, sheet_name='Master Data')
                    print(f"  📑 Reading from 'Master Data' sheet...")
                except:
                    try:
                        df = pd.read_excel(filename)
                        print(f"  📑 Reading from default sheet...")
                    except Exception as e:
                        print(f"  ⚠️ Error reading file: {e}")
                        return
                
                if 'Real_Phone_Number' in df.columns:
                    # Get all non-empty phone numbers
                    existing_phones = df['Real_Phone_Number'].dropna().astype(str)
                    existing_phones = existing_phones[existing_phones != '']
                    
                    # Clean and normalize phone numbers for comparison
                    for phone in existing_phones:
                        # Remove spaces, dashes, dots for comparison
                        cleaned_phone = re.sub(r'[\s\-\.\(\)]', '', str(phone))
                        self.existing_phones.add(cleaned_phone)
                    
                    print(f"  ✅ Found {len(self.existing_phones)} existing phone numbers")
                    print(f"  📞 Sample existing phones: {list(self.existing_phones)[:5]}...")
                else:
                    print(f"  ℹ️ No 'Real_Phone_Number' column found in {filename}")
            else:
                print(f"  ℹ️ {filename} doesn't exist yet - starting fresh")
                
        except Exception as e:
            print(f"  ⚠️ Error loading existing phones: {e}")
            self.existing_phones = set()
    
    def is_phone_duplicate(self, phone_number):
        """Check if a phone number already exists"""
        if not phone_number:
            return False
        
        # Clean the phone number for comparison
        cleaned_phone = re.sub(r'[\s\-\.\(\)]', '', str(phone_number))
        
        # Check both with and without +971 prefix
        variations = [
            cleaned_phone,
            cleaned_phone.replace('+971', '971'),
            cleaned_phone.replace('971', '+971'),
            cleaned_phone.replace('+971', '0') if cleaned_phone.startswith('+971') else None
        ]
        
        # Remove None values
        variations = [v for v in variations if v]
        
        # Check if any variation exists
        for variation in variations:
            if variation in self.existing_phones:
                return True
        
        return False
        
    def handle_captcha(self):
        """Handle CAPTCHA if present"""
        if self.driver is None:
            return False
        title = self.driver.title.lower()
        if any(word in title for word in ['pardon', 'interruption', 'captcha', 'verify', 'security']):
            print("\n🚨 CAPTCHA DETECTED!")
            print("📱 Please solve it in the browser window")
            input("Press Enter after solving CAPTCHA...")
            return True
        return True
    
    def find_car_listings(self, search_url):
        """Find individual car listing URLs from ALL pages of search results"""
        print(f"🔍 Visiting search results: {search_url}")
        
        all_car_urls = set()
        page_num = 1
        
        while True:
            # Construct URL for current page
            if page_num == 1:
                current_url = search_url
            else:
                # Add page parameter to URL
                separator = '&' if '?' in search_url else '?'
                current_url = f"{search_url}{separator}page={page_num}"
            
            print(f"📄 Scraping page {page_num}: {current_url}")
            
            try:
                self.driver.get(current_url)
                time.sleep(5)
                
                self.handle_captcha()
                
                # Scroll to load content
                for i in range(3):
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                
                # Check if this page has any car listings
                page_source = self.driver.page_source
                
                # Pattern for individual car listings with date in URL
                url_pattern = r'/motors/used-cars/[^/]+/[^/]+/\d{4}/\d{1,2}/\d{1,2}/[^"\'>\s]+'
                matches = re.findall(url_pattern, page_source)
                
                page_car_urls = set()
                for match in matches:
                    if not match.startswith('http'):
                        full_url = 'https://dubai.dubizzle.com' + match
                        page_car_urls.add(full_url)
                
                print(f"  ✅ Found {len(page_car_urls)} cars on page {page_num}")
                
                # If no cars found on this page, we've reached the end
                if len(page_car_urls) == 0:
                    print(f"  🏁 No more cars found. Finished at page {page_num-1}")
                    break
                
                # Add to our collection
                all_car_urls.update(page_car_urls)
                
                # Check if there's a "Next" button (Dubizzle uses arrow-based pagination)
                try:
                    # Dubizzle-specific pagination selectors
                    next_button_selectors = [
                        'a[data-testid="page-next"]',
                        'a[class*="next_button"]',
                        '.next_button',
                        'a[title*="next page"]'
                    ]
                    
                    has_next = False
                    for selector in next_button_selectors:
                        try:
                            next_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for element in next_elements:
                                if element.is_displayed():
                                    # Check if the next button is enabled (not disabled)
                                    disabled = element.get_attribute('disabled')
                                    href = element.get_attribute('href')
                                    
                                    # Button is clickable if it's not disabled and has an href
                                    if not disabled and href:
                                        print(f"  ➡️ Found active next button: {selector}")
                                        has_next = True
                                        break
                                    else:
                                        print(f"  ⏸️ Found disabled next button: {selector}")
                            
                            if has_next:
                                break
                                
                        except Exception as e:
                            continue
                    
                    if not has_next:
                        print(f"  🏁 No active 'Next' button found. Finished at page {page_num}")
                        break
                        
                except Exception as e:
                    print(f"  ⚠️ Could not check for next page: {e}")
                    # Continue anyway, let the empty results stop us
                
                page_num += 1
                
                # Safety limit to prevent infinite loops
                if page_num > 50:
                    print(f"  ⚠️ Reached safety limit of 50 pages")
                    break
                    
            except Exception as e:
                print(f"❌ Error on page {page_num}: {e}")
                break
        
        print(f"🎉 TOTAL FOUND: {len(all_car_urls)} individual car listings across {page_num-1} pages")
        return list(all_car_urls)
    
    def get_real_phone_number(self, car_url):
        """Visit car page and click call button to get REAL phone number"""
        result = {
            'URL': car_url,
            'Title': '',
            'Price': '',
            'Real_Phone_Number': '',
            'Fake_Phone_Before': '',
            'Button_Clicked': 'No',
            'Phone_Revealed': 'No',
            'Date_Scraped': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            print(f"\n🚗 Visiting: {car_url}")
            self.driver.get(car_url)
            time.sleep(4)
            
            self.handle_captcha()
            
            # Extract basic info
            result['Title'] = self.get_title()
            result['Price'] = self.get_price()
            
            print(f"📋 Title: {result['Title'][:50]}...")
            print(f"💰 Price: {result['Price']}")
            
            # STEP 1: Check what phone number is visible BEFORE clicking
            phone_before = self.find_visible_phone()
            result['Fake_Phone_Before'] = phone_before
            print(f"📞 Phone BEFORE clicking: {phone_before}")
            
            # STEP 2: Find and click the call button
            print(f"\n🔘 SEARCHING FOR CALL BUTTON...")
            
            call_button_found = self.find_and_click_call_button()
            result['Button_Clicked'] = 'Yes' if call_button_found else 'No'
            
            if call_button_found:
                print("✅ Call button clicked successfully!")
                
                # STEP 3: Wait and look for the revealed phone number
                print("⏳ Waiting for real phone number to appear...")
                time.sleep(5)  # Wait for phone number to load
                
                # Look for the real phone number after clicking
                real_phone = self.extract_phone_after_click()
                result['Real_Phone_Number'] = real_phone
                result['Phone_Revealed'] = 'Yes' if real_phone else 'No'
                
                if real_phone:
                    print(f"🎉 REAL PHONE NUMBER FOUND: {real_phone}")
                else:
                    print("❌ No real phone number appeared after clicking")
                    
            else:
                print("❌ Could not find or click call button")
            
        except Exception as e:
            print(f"❌ Error processing {car_url}: {e}")
        
        return result
    
    def find_and_click_call_button(self):
        """Find and click the call/phone button"""
        
        # Comprehensive list of possible call button selectors
        call_button_selectors = [
            # Specific Dubizzle selectors (most likely)
            'button[data-testid*="phone"]',
            'button[data-testid*="call"]',
            'button[data-testid*="contact"]',
            '[data-testid="contact-button-phone"]',
            
            # Generic button selectors
            'button[class*="phone"]',
            'button[class*="call"]',
            'button[class*="contact"]',
            'a[class*="phone"]',
            'a[class*="call"]',
            
            # Text-based selectors
            'button[aria-label*="phone"]',
            'button[aria-label*="call"]',
            'button[title*="phone"]',
            'button[title*="call"]',
            
            # Generic approach - look for any button with call/phone text
            'button',
            'a[role="button"]',
            'div[role="button"]'
        ]
        
        for selector in call_button_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                print(f"  📋 Checking {len(elements)} elements with selector: {selector}")
                
                for element in elements:
                    try:
                        # Get all text and attributes to check if it's a call button
                        element_text = (element.text or '').lower()
                        element_class = (element.get_attribute('class') or '').lower()
                        element_id = (element.get_attribute('id') or '').lower()
                        element_aria = (element.get_attribute('aria-label') or '').lower()
                        element_title = (element.get_attribute('title') or '').lower()
                        element_data_testid = (element.get_attribute('data-testid') or '').lower()
                        
                        # Combine all text to search
                        all_text = f"{element_text} {element_class} {element_id} {element_aria} {element_title} {element_data_testid}"
                        
                        # Check if this element is related to phone/call
                        call_keywords = [
                            'call', 'phone', 'contact', 'show', 'reveal', 'number',
                            'tel:', 'telephone', 'mobile', 'whatsapp'
                        ]
                        
                        if any(keyword in all_text for keyword in call_keywords):
                            print(f"  🎯 Found potential call button!")
                            print(f"      Text: '{element_text}'")
                            print(f"      Class: '{element_class}'")
                            print(f"      Data-testid: '{element_data_testid}'")
                            
                            # Try to click this element
                            if self.click_button_safely(element):
                                print(f"  ✅ Successfully clicked call button!")
                                return True
                            else:
                                print(f"  ❌ Failed to click this button")
                                
                    except Exception as e:
                        continue
                        
            except Exception as e:
                continue
        
        # Last resort: try clicking anything that might be a phone button
        print(f"  🔄 Last resort: Looking for any clickable element with phone text...")
        try:
            xpath_selectors = [
                "//*[contains(text(), 'call') or contains(text(), 'Call') or contains(text(), 'CALL')]",
                "//*[contains(text(), 'phone') or contains(text(), 'Phone') or contains(text(), 'PHONE')]",
                "//*[contains(text(), 'contact') or contains(text(), 'Contact') or contains(text(), 'CONTACT')]",
                "//*[contains(text(), 'show') or contains(text(), 'Show') or contains(text(), 'SHOW')]"
            ]
            
            for xpath in xpath_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, xpath)
                    for element in elements:
                        if element.is_displayed():
                            print(f"  🔄 Trying to click: '{element.text}'")
                            if self.click_button_safely(element):
                                print(f"  ✅ Success with xpath approach!")
                                return True
                except:
                    continue
                    
        except:
            pass
        
        print(f"  ❌ No call button found with any method")
        return False
    
    def click_button_safely(self, element):
        """Try multiple methods to click an element"""
        try:
            # Method 1: Scroll to element and normal click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(1)
            element.click()
            time.sleep(2)
            return True
        except:
            try:
                # Method 2: JavaScript click
                self.driver.execute_script("arguments[0].click();", element)
                time.sleep(2)
                return True
            except:
                try:
                    # Method 3: ActionChains
                    actions = ActionChains(self.driver)
                    actions.move_to_element(element).click().perform()
                    time.sleep(2)
                    return True
                except:
                    return False
    
    def find_visible_phone(self):
        """Find any phone number currently visible on the page"""
        try:
            page_text = self.driver.page_source
            
            # Phone patterns
            patterns = [
                r'\+971[\s\-\.]?\d{1,2}[\s\-\.]?\d{3}[\s\-\.]?\d{4}',
                r'971[\s\-\.]?\d{1,2}[\s\-\.]?\d{3}[\s\-\.]?\d{4}',
                r'0\d{1,2}[\s\-\.]?\d{3}[\s\-\.]?\d{4}',
                r'\b\d{10,11}\b'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    return matches[0]
                    
        except:
            pass
        
        return ''
    
    def extract_phone_after_click(self, wait_time=5):
        """Extract phone number that appears after clicking call button"""
        print(f"⏳ Waiting {wait_time}s for phone number to appear...")
        
        for attempt in range(wait_time):
            time.sleep(1)
            
            try:
                # Method 1: Look for popup/modal phone numbers (this is where the real numbers appear)
                popup_selectors = [
                    '[role="dialog"] *',  # Inside dialog
                    '.modal *',  # Inside modal
                    '[class*="modal"] *',  # Inside any modal class
                    '[class*="popup"] *',  # Inside any popup class
                    '[class*="phone"] *',  # Inside phone-related classes
                    '[data-testid*="phone"] *',  # Inside phone test elements
                ]
                
                for selector in popup_selectors:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed():
                                text = element.text.strip()
                                # Look for UAE phone numbers in popup
                                phone_match = re.search(r'\+971[\s\-\.]?\d{1,2}[\s\-\.]?\d{3}[\s\-\.]?\d{4}', text)
                                if phone_match:
                                    phone = phone_match.group(0)
                                    print(f"🎉 Found phone in popup: {phone}")
                                    return phone
                    except:
                        continue
                
                # Method 2: Look for any new phone numbers that appeared after clicking
                all_text = self.driver.page_source
                uae_phones = re.findall(r'\+971[\s\-\.]?\d{1,2}[\s\-\.]?\d{3}[\s\-\.]?\d{4}', all_text)
                
                if uae_phones:
                    # Return the first UAE format phone (most likely to be real)
                    phone = uae_phones[0]
                    print(f"🎉 Found UAE format phone: {phone}")
                    return phone
                
                # Method 3: Look for phone number containers that might have updated
                phone_containers = [
                    '[class*="phone"]',
                    '[data-testid*="phone"]',
                    '[class*="contact"]',
                    '[data-testid*="contact"]'
                ]
                
                for selector in phone_containers:
                    try:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for element in elements:
                            if element.is_displayed():
                                text = element.text.strip()
                                # Look for any phone pattern
                                phone_patterns = [
                                    r'\+971[\s\-\.]?\d{1,2}[\s\-\.]?\d{3}[\s\-\.]?\d{4}',
                                    r'971[\s\-\.]?\d{1,2}[\s\-\.]?\d{3}[\s\-\.]?\d{4}',
                                    r'0\d{1,2}[\s\-\.]?\d{3}[\s\-\.]?\d{4}'
                                ]
                                
                                for pattern in phone_patterns:
                                    phone_match = re.search(pattern, text)
                                    if phone_match:
                                        phone = phone_match.group(0)
                                        # Skip obvious fake numbers
                                        if not re.match(r'^0+$', phone.replace('+', '').replace('-', '').replace(' ', '').replace('.', '')):
                                            print(f"🎉 Found phone in container: {phone}")
                                            return phone
                    except:
                        continue
                
            except Exception as e:
                print(f"❌ Error during attempt {attempt + 1}: {e}")
                continue
        
        print(f"❌ No phone number found after {wait_time} attempts")
        return None
    
    def get_title(self):
        """Extract title"""
        selectors = ['h1', '[class*="title"]']
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text and len(text) > 5:
                    return text
            except:
                continue
        return ''
    
    def get_price(self):
        """Extract price"""
        selectors = ['[data-testid="listing-price"]', '[class*="price"]']
        for selector in selectors:
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text and ('aed' in text.lower() or any(c.isdigit() for c in text)):
                    return text
            except:
                continue
        return ''
    
    def scrape_with_real_phones(self, search_url, max_cars=10):
        """Main scraping method focusing on real phone numbers"""
        print("🚀 CLICK CALL BUTTON SCRAPER")
        print("🎯 Focus: Getting REAL phone numbers by clicking call buttons")
        print("🔄 Duplicate Detection: Skip listings with existing phone numbers")
        
        # Load existing phone numbers to avoid duplicates
        filename = "Dubizzle Data.xlsx"
        self.load_existing_phone_numbers(filename)
        
        self.setup_driver()
        
        try:
            # Find car listings
            car_urls = self.find_car_listings(search_url)
            
            if not car_urls:
                print("❌ No car listings found")
                return
            
            print(f"\n📋 Processing up to {max_cars} cars from {len(car_urls)} found")
            
            processed_count = 0
            skipped_count = 0
            
            # Process each car
            for i, car_url in enumerate(car_urls, 1):
                print(f"\n{'='*80}")
                print(f"🚗 CHECKING CAR {i}/{len(car_urls)}")
                print(f"{'='*80}")
                
                # First, do a quick check to see if we can get the phone number without processing
                try:
                    print(f"🔍 Quick phone check: {car_url}")
                    self.driver.get(car_url)
                    time.sleep(3)
                    
                    # Get the initial phone number visible on page
                    initial_phone = self.find_visible_phone()
                    
                    # Check if this phone (or the real one) might be a duplicate
                    if initial_phone and self.is_phone_duplicate(initial_phone):
                        print(f"📞 Initial phone found: {initial_phone}")
                        print(f"⏭️  SKIPPING: Phone number already exists in database")
                        skipped_count += 1
                        continue
                    
                    # If we have fewer than processed limit, continue with full processing
                    if processed_count >= max_cars:
                        print(f"✅ Reached processing limit of {max_cars} new cars")
                        break
                        
                    print(f"🔄 PROCESSING CAR {processed_count + 1} (NEW)")
                    
                except Exception as e:
                    print(f"⚠️ Error during quick check: {e}")
                    # Continue with full processing anyway
                
                # Full processing
                car_data = self.get_real_phone_number(car_url)
                
                # Check if the real phone number is a duplicate
                if car_data['Real_Phone_Number'] and self.is_phone_duplicate(car_data['Real_Phone_Number']):
                    print(f"⏭️  SKIPPING: Real phone {car_data['Real_Phone_Number']} already exists")
                    skipped_count += 1
                    continue
                
                # Add to our data if it's new
                self.scraped_data.append(car_data)
                processed_count += 1
                
                # Show results
                if car_data['Real_Phone_Number']:
                    print(f"🎉 SUCCESS: New phone = {car_data['Real_Phone_Number']}")
                    # Add to existing phones set to avoid duplicates within this session
                    cleaned_phone = re.sub(r'[\s\-\.\(\)]', '', str(car_data['Real_Phone_Number']))
                    self.existing_phones.add(cleaned_phone)
                else:
                    print(f"❌ FAILED: No real phone number obtained")
                
                # Stop if we've processed enough new cars
                if processed_count >= max_cars:
                    print(f"✅ Reached processing limit of {max_cars} new cars")
                    break
                
                # Delay between cars
                delay = random.uniform(6, 10)
                print(f"⏳ Waiting {delay:.1f} seconds...")
                time.sleep(delay)
            
            print(f"\n🎉 Scraping completed!")
            print(f"📊 Summary:")
            print(f"  - Total cars checked: {i}")
            print(f"  - New cars processed: {processed_count}")
            print(f"  - Duplicates skipped: {skipped_count}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            if self.driver:
                self.driver.quit()
    
    def save_results(self, filename='real_phone_numbers.xlsx'):
        """Save results to Excel with multiple sheets: Master Data + New Numbers Only"""
        if not self.scraped_data:
            print("❌ No new data to save")
            return
        
        new_df = pd.DataFrame(self.scraped_data)
        
        # Check if file exists and has data
        if os.path.exists(filename):
            try:
                # Read existing master data (try different sheet names for compatibility)
                try:
                    existing_df = pd.read_excel(filename, sheet_name='Master Data')
                    print(f"📋 Found existing 'Master Data' sheet with {len(existing_df)} records")
                except:
                    # Fallback to default sheet if 'Master Data' doesn't exist
                    existing_df = pd.read_excel(filename)
                    print(f"📋 Found existing data with {len(existing_df)} records (converting to Master Data sheet)")
                
                # Combine existing and new data
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                print(f"➕ Adding {len(new_df)} new records to Master Data")
                
            except Exception as e:
                print(f"⚠️ Error reading existing file: {e}")
                print("📝 Creating new file with current data")
                combined_df = new_df
        else:
            print("📝 Creating new file")
            combined_df = new_df
        
        # Create ExcelWriter to handle multiple sheets
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Sheet 1: Master Data (all data combined)
            combined_df.to_excel(writer, sheet_name='Master Data', index=False)
            print(f"💾 Saved Master Data sheet with {len(combined_df)} total records")
            
            # Sheet 2: New Numbers Only (current session data)
            new_df.to_excel(writer, sheet_name='New Numbers Only', index=False)
            print(f"🆕 Saved 'New Numbers Only' sheet with {len(new_df)} new records")
            
            # Sheet 3: Phone Numbers Summary (just the phone numbers for easy reference)
            if len(new_df[new_df['Real_Phone_Number'] != '']) > 0:
                phone_summary = new_df[new_df['Real_Phone_Number'] != ''][['Real_Phone_Number', 'Title', 'Price', 'URL', 'Date_Scraped']].copy()
                phone_summary = phone_summary.rename(columns={'Real_Phone_Number': 'Phone Number'})
                phone_summary.to_excel(writer, sheet_name='New Phones Summary', index=False)
                print(f"📞 Saved 'New Phones Summary' sheet with {len(phone_summary)} phone numbers")
        
        # Calculate statistics for new data only
        new_total = len(new_df)
        new_real_phones = len(new_df[new_df['Real_Phone_Number'] != ''])
        new_buttons_clicked = len(new_df[new_df['Button_Clicked'] == 'Yes'])
        
        # Calculate statistics for all data
        total_records = len(combined_df)
        total_real_phones = len(combined_df[combined_df['Real_Phone_Number'] != ''])
        
        print(f"\n✅ RESULTS SAVED TO {filename}")
        print(f"📊 WORKBOOK CONTAINS:")
        print(f"  📑 'Master Data' sheet: {total_records} total records")
        print(f"  🆕 'New Numbers Only' sheet: {new_total} new records")
        if new_real_phones > 0:
            print(f"  📞 'New Phones Summary' sheet: {new_real_phones} new phone numbers")
        
        print(f"\n📊 SESSION SUMMARY:")
        print(f"  - New cars processed: {new_total}")
        print(f"  - New call buttons clicked: {new_buttons_clicked}")
        print(f"  - New real phone numbers: {new_real_phones}")
        if new_total > 0:
            print(f"  - Session success rate: {(new_real_phones/new_total*100):.1f}%")
        
        print(f"\n📈 TOTAL DATABASE:")
        print(f"  - Total records: {total_records}")
        print(f"  - Total real phone numbers: {total_real_phones}")
        if total_records > 0:
            print(f"  - Overall success rate: {(total_real_phones/total_records*100):.1f}%")
        
        if new_real_phones > 0:
            print(f"\n📞 NEW PHONE NUMBERS ADDED THIS SESSION:")
            for _, row in new_df[new_df['Real_Phone_Number'] != ''].iterrows():
                print(f"  {row['Real_Phone_Number']} - {row['Title'][:50]}...")


def main():
    """Main function"""
    print("🚀 CLICK CALL BUTTON SCRAPER WITH DUPLICATE DETECTION & MULTI-SHEET EXCEL")
    print("="*80)
    print("🎯 This scraper will:")
    print("1. Load existing phone numbers from 'Master Data' sheet")
    print("2. Find individual car listings from ALL pages")
    print("3. Quick check each car for duplicate phone numbers")
    print("4. SKIP cars with existing phone numbers")
    print("5. For new cars: visit page, click 'Call' button")
    print("6. Extract REAL phone numbers that appear")
    print("7. Save to Excel with 3 sheets:")
    print("   📑 'Master Data' - All data (existing + new)")
    print("   🆕 'New Numbers Only' - Current session data")
    print("   📞 'New Phones Summary' - Clean phone list")
    print("8. Show summary of new vs duplicate/skipped cars")
    print("="*80)
    
    url = input("\nEnter your Dubizzle filtered URL: ").strip()
    if not url:
        print("❌ Please provide a URL")
        return
    
    max_cars = input("How many cars to process? [ALL]: ").strip()
    if max_cars.upper() == "ALL" or not max_cars:
        max_cars = 999999  # Process all found cars
    else:
        max_cars = int(max_cars) if max_cars.isdigit() else 999999
    
    # Always use the same filename
    filename = "Dubizzle Data.xlsx"
    print(f"\n📁 Results will be saved to: {filename}")
    
    scraper = ClickCallScraper(headless=False)
    
    try:
        scraper.scrape_with_real_phones(url, max_cars)
        scraper.save_results(filename)
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        if scraper.scraped_data:
            scraper.save_results(filename)


if __name__ == "__main__":
    main() 
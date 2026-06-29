import requests
from bs4 import BeautifulSoup
import re
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import engine, Car, init_db
from sqlalchemy.orm import Session

BASE_URL = "https://www.pakwheels.com/used-cars/search/-/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

PUNJAB_CITIES = [
    "lahore", "faisalabad", "rawalpindi", "multan", "gujranwala",
    "sialkot", "bahawalpur", "sargodha", "rahim yar khan", "gujrat"
]

def parse_clean_price(price_str):
    try:
        cleaned = price_str.lower().replace("pkr", "").replace(",", "").strip()
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", cleaned)
        if not numbers:
            return 0
        val = float(numbers[0])
        if "lac" in cleaned:
            return int(val * 100000)
        if "crore" in cleaned:
            return int(val * 10000000)
        return int(val)
    except:
        return 0

def extract_year_from_title(title_str):
    match = re.search(r'\b(19\d\d|20\d\d)\b', title_str)
    return int(match.group(0)) if match else 2020

def scrape_and_store_live(pages=2):
    init_db()
    total_inserted = 0
    
    with Session(engine) as session:
        for page in range(1, pages + 1):
            try:
                response = requests.get(f"{BASE_URL}?page={page}", headers=HEADERS, timeout=10)
                # CRITICAL BUG FIXED: removed response.status_check
                if response.status_code != 200:
                    response.raise_for_status()
                
                soup = BeautifulSoup(response.text, "html.parser")
                listings = soup.find_all("li", class_="classified-listing")
                
                for item in listings:
                    try:
                        title_elem = item.find("a", class_="car-name")
                        if not title_elem:
                            continue
                        title = title_elem.get_text(strip=True)
                        
                        price_details_elem = item.find("div", class_="price-details")
                        if not price_details_elem:
                            continue
                        price_raw = price_details_elem.get_text(strip=True)
                        
                        details = item.find_all("ul", class_="search-vehicle-info")
                        city = "Unknown"
                        if details and len(details[0].find_all("li")) >= 1:
                            city = details[0].find_all("li")[-1].get_text(strip=True)
                        
                        clean_price = parse_clean_price(price_raw)
                        year = extract_year_from_title(title)
                        
                        words = title.split()
                        make = words[0] if len(words) > 0 else "Unknown"
                        model = words[1] if len(words) > 1 else "Car"
                        
                        province = "Punjab" if city.lower().strip() in PUNJAB_CITIES else "Other"
                        
                        exists = session.query(Car).filter(Car.title == title, Car.price == clean_price, Car.city == city).first()
                        if exists:
                            continue
                            
                        car_record = Car(
                            title=title, make=make, model=model,
                            price=clean_price, year=year, city=city, province=province
                        )
                        session.add(car_record)
                        total_inserted += 1
                    except Exception:
                        continue
                session.commit()
            except Exception as e:
                print(f"[ERROR] Failed handling batch processing page {page}: {e}")
                continue
                
    print(f"[SUCCESS] Scraper execution ended. Added {total_inserted} brand new listings.")

if __name__ == "__main__":
    scrape_and_store_live(pages=3)

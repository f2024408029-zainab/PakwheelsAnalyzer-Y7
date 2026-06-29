from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import query_filtered_cars, evaluate_car_deal, get_market_dashboard_stats, init_db
from scraper.scraper import scrape_and_store_live

app = Flask(__name__)
CORS(app)

@app.route('/api/scrape', methods=['POST'])
def trigger_scraper():
    """Triggers Scraper script dynamically"""
    scrape_and_store_live()
    return jsonify({"status": "Database successfully populated with clean live data!"})

@app.route('/api/cars', methods=['GET'])
def get_cars():
    """Route supporting normal dynamic filters (Province, Model, Year)"""
    prov = request.args.get('province')
    mod = request.args.get('model')
    yr = request.args.get('year')
    return jsonify(query_filtered_cars(province=prov, model=mod, year=yr))

@app.route('/api/analytics/evaluate', methods=['GET'])
def check_deal():
    """Route for Feature 1: Fair Price Evaluator Engine"""
    make = request.args.get('make')
    model = request.args.get('model')
    year = request.args.get('year')
    price = request.args.get('price')

    if not all([make, model, year, price]):
        return jsonify({"error": "Missing parameters. Required: make, model, year, price"}), 400

    evaluation = evaluate_car_deal(make, model, int(year), int(price))
    return jsonify(evaluation)

@app.route('/api/analytics/dashboard', methods=['GET'])
def get_dashboard_summary():
    """Route for Feature 2: High-level KPI Analytics Summary"""
    return jsonify(get_market_dashboard_stats())

if __name__ == '__main__':
    init_db()  # Ensures structures exist right out of the box
    app.run(debug=True, port=8000)


SCRAPER:
import requests
from bs4 import BeautifulSoup
import re
import sys
import os

# Align dynamic sys paths so it seamlessly locates your partner's 'database' module
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
    """Normalizes string amounts like 'PKR 28.75 lacs' or '1.1 crore' into pure numeric integers"""
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
    """Robust fallback: if the year badge fails to parse, extract the 4-digit year from the headline text"""
    match = re.search(r'\b(19\d\d|20\d\d)\b', title_str)
    return int(match.group(0)) if match else 2020

def scrape_and_store_live(pages=2):
    """Scrapes PakWheels listings, sanitizes formatting, maps regional provinces, and saves to DB"""
    init_db()
    total_inserted = 0
   
    with Session(engine) as session:
        for page in range(1, pages + 1):
            try:
                response = requests.get(f"{BASE_URL}?page={page}", headers=HEADERS, timeout=10)
                if response.status_check != 200 and response.status_code != 200:
                    response.raise_for_status()
               
                soup = BeautifulSoup(response.text, "html.parser")
                listings = soup.find_all("li", class_="classified-listing")
               
                for item in listings:
                    try:
                        title_elem = item.find("a", class_="car-name")
                        if not title_elem:
                            continue
                        title = title_elem.get_text(strip=True)
                       
                        price_raw = item.find("div", class_="price-details").get_text(strip=True)
                       
                        # Fix broken parsing values by mapping safely
                        details = item.find_all("ul", class_="search-vehicle-info")
                        city = "Unknown"
                        if details and len(details[0].find_all("li")) >= 1:
                            city = details[0].find_all("li")[-1].get_text(strip=True)
                       
                        # Process cleansed data elements
                        clean_price = parse_clean_price(price_raw)
                        year = extract_year_from_title(title)
                       
                        words = title.split()
                        make = words[0] if len(words) > 0 else "Unknown"
                        model = words[1] if len(words) > 1 else "Car"
                       
                        province = "Punjab" if city.lower().strip() in PUNJAB_CITIES else "Other"
                       
                        # Check duplicate prevention
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
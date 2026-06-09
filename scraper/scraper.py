import requests
from bs4 import BeautifulSoup
import csv
import os

BASE_URL = "https://www.pakwheels.com/used-cars/search/-/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

def fetch_page(url):
    """Fetch HTML content from a given URL."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"[ERROR] Failed to fetch page: {e}")
        return None

def parse_listings(html):
    """Parse car listings from HTML and return list of dicts."""
    soup = BeautifulSoup(html, "html.parser")
    cars = []

    listings = soup.find_all("li", class_="classified-listing")

    for listing in listings:
        try:
            title = listing.find("a", class_="car-name")
            title = title.get_text(strip=True) if title else "N/A"

            price = listing.find("div", class_="price-details")
            price = price.get_text(strip=True) if price else "N/A"

            details = listing.find_all("ul", class_="search-vehicle-info")
            year, mileage, city = "N/A", "N/A", "N/A"
            if details:
                items = details[0].find_all("li")
                if len(items) >= 1:
                    year = items[0].get_text(strip=True)
                if len(items) >= 2:
                    mileage = items[1].get_text(strip=True)
                if len(items) >= 3:
                    city = items[2].get_text(strip=True)

            cars.append({
                "title": title,
                "price": price,
                "year": year,
                "mileage": mileage,
                "city": city
            })

        except Exception as e:
            print(f"[WARNING] Skipped a listing: {e}")
            continue

    return cars

def save_to_csv(cars, filename="pakwheels_data.csv"):
    """Save scraped car data to a CSV file."""
    if not cars:
        print("[INFO] No data to save.")
        return

    output_path = os.path.join(os.path.dirname(__file__), filename)
    fieldnames = ["title", "price", "year", "mileage", "city"]

    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cars)

    print(f"[INFO] Data saved to {output_path} ({len(cars)} records)")

def run_scraper(pages=3):
    """Main scraper function — scrapes multiple pages."""
    all_cars = []

    for page in range(1, pages + 1):
        url = f"{BASE_URL}?page={page}"
        print(f"[INFO] Scraping page {page}: {url}")

        html = fetch_page(url)
        if html:
            cars = parse_listings(html)
            all_cars.extend(cars)
            print(f"[INFO] Found {len(cars)} listings on page {page}")

    save_to_csv(all_cars)
    return all_cars

if __name__ == "__main__":
    run_scraper(pages=3)
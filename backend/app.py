from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# Align dynamic paths correctly (Moving up 1 level from backend/ to root)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import query_filtered_cars, evaluate_car_deal, get_market_dashboard_stats, init_db
from scraper.scraper import scrape_and_store_live

app = Flask(__name__)
CORS(app)

@app.route('/api/scrape', methods=['POST'])
def trigger_scraper():
    """Triggers Scraper script dynamically"""
    try:
        scrape_and_store_live(pages=2)
        return jsonify({"status": "Database successfully populated with clean live data!"})
    except Exception as e:
        return jsonify({"error": f"Scraper failed: {str(e)}"}), 500

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

    try:
        evaluation = evaluate_car_deal(make, model, int(year), int(price))
        return jsonify(evaluation)
    except ValueError:
        return jsonify({"error": "Invalid year or price format. Must be integers."}), 400

@app.route('/api/analytics/dashboard', methods=['GET'])
def get_dashboard_summary():
    """Route for Feature 2: High-level KPI Analytics Summary"""
    stats = get_market_dashboard_stats()
    return jsonify(stats)

if __name__ == '__main__':
    init_db()  
    app.run(debug=True, port=8000)
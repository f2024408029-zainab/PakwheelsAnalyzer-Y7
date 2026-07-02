from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

DATABASE_API_URL = "http://localhost:5000"   # matches backend's new port


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/cars')
def get_cars():
    try:
        response = requests.get(f"{DATABASE_API_URL}/api/cars")
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/search')
def search():
    query = request.args.get('query')
    return jsonify({"results": []})


if __name__ == '__main__':
    app.run(debug=True, port=8000)
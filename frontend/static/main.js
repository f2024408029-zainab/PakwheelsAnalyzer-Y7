const API_BASE = "http://127.0.0.1:5000/api";

async function loadDashboardStats() {
    try {
        let res = await fetch(`${API_BASE}/analytics/dashboard`);
        let data = await res.json();
        if (!data.error && data.most_expensive_car && data.cheapest_car) {
            document.getElementById('stat-total').innerText = data.total_listings;
            document.getElementById('stat-max').innerText = `PKR ${(data.most_expensive_car.price / 100000).toFixed(1)} Lacs`;
            document.getElementById('stat-min').innerText = `PKR ${(data.cheapest_car.price / 100000).toFixed(1)} Lacs`;
        }
    } catch (e) { console.log("Stats fetch error", e); }
}

async function triggerScraper() {
    alert("Live background scraping process started. Please stand by...");
    try {
        let res = await fetch(`${API_BASE}/scrape`, { method: 'POST' });
        let data = await res.json();
        alert(data.status || data.error);
        loadDashboardStats();
        fetchFilteredCars();
    } catch (e) { alert("Failed to trigger scraper. Is the backend (port 5000) running?"); }
}

async function fetchFilteredCars() {
    let prov = document.getElementById('filter-province').value;
    let model = document.getElementById('filter-model').value;

    let url = `${API_BASE}/cars?province=${prov}&model=${model}`;
    try {
        let res = await fetch(url);
        let cars = await res.json();

        let html = "";
        if (!cars || cars.length === 0) {
            html = `<tr><td colspan="5" class="text-center text-muted">No database logs matched conditions.</td></tr>`;
        } else {
            cars.forEach(car => {
                html += `<tr>
                    <td class="fw-semibold">${car.title}</td>
                    <td>${car.city}</td>
                    <td><span class="badge bg-secondary">${car.province}</span></td>
                    <td>${car.year}</td>
                    <td class="text-primary fw-bold">PKR ${(car.price / 100000).toFixed(2)} Lacs</td>
                </tr>`;
            });
        }
        document.getElementById('car-table-body').innerHTML = html;
    } catch (e) { console.log("Error fetching cars data.", e); }
}

async function evaluateDeal() {
    let make = document.getElementById('eval-make').value;
    let model = document.getElementById('eval-model').value;
    let year = document.getElementById('eval-year').value;
    let price = document.getElementById('eval-price').value;
    try {
        let res = await fetch(`${API_BASE}/analytics/evaluate?make=${make}&model=${model}&year=${year}&price=${price}`);
        let data = await res.json();

        let div = document.getElementById('eval-result');
        div.classList.remove('d-none', 'alert-success', 'alert-danger', 'alert-warning', 'alert-secondary');

        if (data.status === "Success") {
            div.innerText = `Market Evaluation: ${data.deal_evaluation} (Average Market Price: PKR ${(data.market_average / 100000).toFixed(1)} Lacs)`;
            if (data.deal_evaluation.includes("Great")) div.classList.add('alert-success');
            else if (data.deal_evaluation.includes("Overpriced")) div.classList.add('alert-danger');
            else div.classList.add('alert-warning');
        } else {
            div.innerText = data.message || data.error;
            div.classList.add('alert-secondary');
        }
    } catch (e) { console.log("Evaluation request failed.", e); }
}

window.onload = () => {
    loadDashboardStats();
    fetchFilteredCars();
};
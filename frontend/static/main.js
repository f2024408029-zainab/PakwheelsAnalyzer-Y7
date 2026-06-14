async function searchCars() {
    const query = document.getElementById('searchInput').value;
    try {
        const response = await fetch(`/api/search?query=${query}`);
        const data = await response.json();
        displayResults(data.results);
    } catch (error) {
        console.error('Error:', error);
    }
}

function displayResults(results) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = results.map(car => `
        <div class="car-card">
            <h3>${car.model}</h3>
            <p>Price: Rs. ${car.price}</p>
            <p>Year: ${car.year}</p>
        </div>
    `).join('');
}
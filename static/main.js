document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('search-form');
    const weightSlider = document.getElementById('weight-slider');
    const weightValue = document.getElementById('weight-value');
    const pcaSlider = document.getElementById('pca-slider');
    const pcaValue = document.getElementById('pca-value');
    const errorDiv = document.getElementById('error');

    weightSlider.addEventListener('input', (e) => {
        weightValue.textContent = e.target.value;
    });

    pcaSlider.addEventListener('input', (e) => {
        pcaValue.textContent = e.target.value;
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        errorDiv.style.display = 'none';

        const formData = new FormData();
        const textQuery = document.getElementById('query').value;
        const imageFile = document.getElementById('image-input').files[0];
        
        if (!textQuery && !imageFile) {
            errorDiv.textContent = 'Please provide either a text query or an image';
            errorDiv.style.display = 'block';
            return;
        }

        if (textQuery) formData.append('text_query', textQuery);
        if (imageFile) formData.append('image_query', imageFile);
        formData.append('text_weight', weightSlider.value);
        formData.append('num_components', pcaSlider.value);

        try {
            const response = await fetch('/search', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('Search failed');
            
            const data = await response.json();
            displayResults(data.results);
        } catch (error) {
            errorDiv.textContent = 'An error occurred during search';
            errorDiv.style.display = 'block';
        }
    });
});

function displayResults(results) {
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '';

    const grid = document.createElement('div');
    grid.className = 'results-grid';

    results.forEach(result => {
        const card = document.createElement('div');
        card.className = 'result-card';

        const img = document.createElement('img');
        img.src = `/images/${result.image_path}`;
        img.alt = 'Search result';

        const info = document.createElement('div');
        info.className = 'result-info';
        info.innerHTML = `
            <div class="similarity-score">
                Similarity: ${result.similarity.toFixed(4)}
            </div>
        `;

        card.appendChild(img);
        card.appendChild(info);
        grid.appendChild(card);
    });

    resultsDiv.appendChild(grid);
}
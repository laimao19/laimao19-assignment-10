document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('search-form');
    const imageInput = document.getElementById('image-input');
    const fileDisplay = document.getElementById('file-display');
    const errorDiv = document.getElementById('error');
    const queryTypeSelect = document.getElementById('query-type');
 
    imageInput.addEventListener('change', (e) => {
        fileDisplay.value = e.target.files[0]?.name || '';
    });
 
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        errorDiv.style.display = 'none';
 
        const formData = new FormData();
        const queryType = queryTypeSelect.value;
        const textQuery = document.getElementById('query').value;
        const imageFile = imageInput.files[0];
        const weight = document.getElementById('weight-slider').value;
 
        if (queryType === 'text' && !textQuery) {
            errorDiv.textContent = 'Please enter a text query';
            errorDiv.style.display = 'block';
            return;
        }
 
        if (queryType === 'image' && !imageFile) {
            errorDiv.textContent = 'Please select an image';
            errorDiv.style.display = 'block';
            return;
        }
 
        if (queryType === 'hybrid' && (!textQuery || !imageFile)) {
            errorDiv.textContent = 'Please provide both text and image for hybrid search';
            errorDiv.style.display = 'block';
            return;
        }
 
        if (textQuery) formData.append('text_query', textQuery);
        if (imageFile) formData.append('image_query', imageFile);
        if (queryType === 'hybrid') formData.append('text_weight', weight);
        
        // Add PCA parameters
        formData.append('use_pca', document.getElementById('use-pca').checked);
        formData.append('num_components', document.getElementById('pca-components').value);
        formData.append('query_type', queryType);
 
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
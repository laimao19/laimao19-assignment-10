from flask import Flask, request, jsonify, send_from_directory, render_template
import torch
import torch.nn.functional as F
from open_clip import create_model_and_transforms
import open_clip
import pandas as pd
from PIL import Image
import os
from sklearn.decomposition import PCA
import numpy as np

app = Flask(__name__, static_folder='static', template_folder='templates')

# Load CLIP model and preprocessing
model, _, preprocess = create_model_and_transforms('ViT-B/32', pretrained='openai')
tokenizer = open_clip.tokenizer.tokenize
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

# Load pre-computed embeddings and prepare PCA
df = pd.read_pickle('image_embeddings.pickle')
embeddings_array = np.array(df['embedding'].tolist())
image_embeddings = torch.tensor(embeddings_array).to(device)

# Initialize and fit PCA
pca = PCA(n_components=50)
pca_embeddings = pca.fit_transform(embeddings_array)

def get_top_k_similar(query_embedding, k=5, use_pca=False, num_components=10):
    with torch.no_grad():
        if use_pca:
            # Transform query to PCA space - handle both single and batch embeddings
            query_np = query_embedding.cpu().numpy()
            if len(query_np.shape) == 1:
                query_np = query_np.reshape(1, -1)
            query_pca = pca.transform(query_np)[:, :num_components]
            query_pca = torch.tensor(query_pca).to(device)
            db_pca = torch.tensor(pca_embeddings[:, :num_components]).to(device)
            similarities = F.cosine_similarity(query_pca.squeeze(), db_pca)
        else:
            similarities = F.cosine_similarity(query_embedding.squeeze(), image_embeddings)
        
        top_k = similarities.topk(k)
        results = []
        for idx, score in zip(top_k.indices.cpu(), top_k.values.cpu()):
            results.append({
                'image_path': df.iloc[int(idx)]['file_name'],
                'similarity': float(score)
            })
        return results

@app.route('/search', methods=['POST'])
def search():
    try:
        text_query = request.form.get('text_query', '')
        text_weight = float(request.form.get('text_weight', 0.8))
        use_pca = request.form.get('use_pca', 'false').lower() == 'true'
        num_components = int(request.form.get('num_components', 10))
        query_type = request.form.get('query_type', 'image')
        
        query_embedding = None
        
        if text_query and query_type in ['text', 'hybrid']:
            text = tokenizer([text_query]).to(device)
            text_embedding = F.normalize(model.encode_text(text))
            query_embedding = text_embedding
        
        if 'image_query' in request.files and query_type in ['image', 'hybrid']:
            image = preprocess(Image.open(request.files['image_query'])).unsqueeze(0).to(device)
            image_embedding = F.normalize(model.encode_image(image))
            
            if query_embedding is not None:
                # For hybrid queries, combine before PCA
                query_embedding = F.normalize(
                    text_weight * text_embedding + 
                    (1.0 - text_weight) * image_embedding
                )
            else:
                query_embedding = image_embedding
        
        # Apply PCA after combining embeddings for hybrid queries
        results = get_top_k_similar(query_embedding, use_pca=use_pca, num_components=num_components)
        return jsonify({'results': results})
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('coco_images_resized', filename)

if __name__ == '__main__':
    app.run(debug=True)
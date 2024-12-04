from flask import Flask, request, jsonify, send_from_directory, render_template
import torch
import torch.nn.functional as F
from open_clip import create_model_and_transforms
import open_clip
import pandas as pd
from PIL import Image
import os

app = Flask(__name__, static_folder='static', template_folder='templates')

# Load CLIP model and preprocessing
model, _, preprocess = create_model_and_transforms('ViT-B/32', pretrained='openai')
tokenizer = open_clip.tokenizer.tokenize
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

# Load pre-computed embeddings
df = pd.read_pickle('image_embeddings.pickle')
image_embeddings = torch.tensor(df['embedding'].tolist()).to(device)

def get_top_k_similar(query_embedding, k=5):
    with torch.no_grad():
        similarities = F.cosine_similarity(query_embedding, image_embeddings)
        top_k = similarities.topk(k)
        results = []
        
        for idx, score in zip(top_k.indices.cpu(), top_k.values.cpu()):
            results.append({
                'image_path': df.iloc[int(idx)]['file_name'],
                'similarity': float(score)
            })
        return results

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    try:
        text_query = request.form.get('text_query', '')
        text_weight = float(request.form.get('text_weight', 0.5))
        
        query_embedding = None
        
        if text_query:
            text = tokenizer([text_query]).to(device)  # Add .to(device)
            text_embedding = F.normalize(model.encode_text(text))
            query_embedding = text_embedding
        
        if 'image_query' in request.files:
            print("Processing image...")  # Debug print
            image = preprocess(Image.open(request.files['image_query'])).unsqueeze(0).to(device)
            image_embedding = F.normalize(model.encode_image(image))
            print("Image processed successfully")  # Debug print
            
            if query_embedding is not None:
                query_embedding = F.normalize(
                    text_weight * text_embedding + 
                    (1.0 - text_weight) * image_embedding
                )
            else:
                query_embedding = image_embedding
        
        results = get_top_k_similar(query_embedding)
        return jsonify({'results': results})
    
    except Exception as e:
        print(f"Error: {str(e)}")  # Debug print
        return jsonify({'error': str(e)}), 500
    

@app.route('/images/<path:filename>')
def serve_image(filename):
    return send_from_directory('coco_images_resized', filename)

if __name__ == '__main__':
    app.run(debug=True)
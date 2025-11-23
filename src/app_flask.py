import os
from flask import Flask, request, jsonify, render_template_string
from PIL import Image
from predict import get_model, predict_pil

app = Flask(__name__)

INDEX_HTML = '''
<!doctype html>
<title>Monkeypox Classifier</title>
<h1>Upload image for prediction</h1>
<form method=post enctype=multipart/form-data action="/predict">
  <input type=file name=image>
  <input type=submit value='Upload'>
</form>
<hr>
<p>API endpoint: POST /predict (form-data field 'image')</p>
'''

@app.route('/')
def index():
    return render_template_string(INDEX_HTML)

@app.route('/predict', methods=['POST'])
def predict():
    if 'image' not in request.files:
        return jsonify({'error':'no image provided'}), 400
    f = request.files['image']
    try:
        img = Image.open(f.stream).convert('RGB')
    except Exception as e:
        return jsonify({'error':'invalid image', 'detail': str(e)}), 400
    try:
        label, confidence, probs = predict_pil(img)
    except Exception as e:
        return jsonify({'error':'model error', 'detail': str(e)}), 500
    return jsonify({'label': label, 'confidence': float(confidence), 'probs': probs})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))

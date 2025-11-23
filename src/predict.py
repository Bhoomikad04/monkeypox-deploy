import os, json
import numpy as np
from PIL import Image
import tensorflow as tf

MODEL_DIR = os.environ.get('MODEL_DIR', '/app/model')
MODEL_H5 = os.path.join(MODEL_DIR, 'final_model.h5')
LABELS_JSON = os.path.join(MODEL_DIR, 'labels.json')

_model = None
_inv_labels = None

def _load_labels():
    global _inv_labels
    if _inv_labels is None:
        if os.path.exists(LABELS_JSON):
            with open(LABELS_JSON, 'r') as f:
                labels = json.load(f)
                _inv_labels = {int(v):k for k,v in labels.items()}
        else:
            _inv_labels = None

def get_model():
    global _model
    if _model is None:
        if os.path.exists(MODEL_H5):
            _model = tf.keras.models.load_model(MODEL_H5)
        elif os.path.isdir(os.path.join(MODEL_DIR, 'saved_model')):
            _model = tf.keras.models.load_model(os.path.join(MODEL_DIR, 'saved_model'))
        else:
            raise FileNotFoundError('No model found. Place final_model.h5 or saved_model/ under /app/model or set MODEL_URL to download.')
        _load_labels()
    return _model

def preprocess(img_pil, img_size=(224,224)):
    img = img_pil.resize(img_size)
    x = np.array(img) / 255.0
    if x.ndim == 2:
        x = np.stack([x,x,x], axis=-1)
    if x.shape[2] == 4:
        x = x[..., :3]
    x = np.expand_dims(x, axis=0).astype(np.float32)
    return x

def predict_pil(img_pil):
    model = get_model()
    x = preprocess(img_pil)
    preds = model.predict(x)[0]
    idx = int(preds.argmax())
    conf = float(preds[idx])
    label = None
    if _inv_labels:
        label = _inv_labels.get(idx, str(idx))
    else:
        label = str(idx)
    return label, conf, preds.tolist()

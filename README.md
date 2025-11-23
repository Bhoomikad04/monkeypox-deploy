# Monkeypox Classifier - Full Project (Render-ready) + Training Notebook

This repository includes:
- A Flask API + Render deployment files (Dockerfile, start.sh)
- A training script `src/train.py` that uses transfer learning (ResNet50)
- A Colab-compatible notebook `train_colab.ipynb` to train the model on Kaggle dataset
- Instructions to upload the trained model to cloud storage and deploy on Render
- Your uploaded research paper (path included below)

**Path to the paper you uploaded (for reference):**
`/mnt/data/IEEE_Conference_paper_team19.pdf`

---

## Quick flow
1. Open `train_colab.ipynb` in Google Colab.
2. Upload your `kaggle.json` API token (or set up Kaggle in Colab) and run the cells to download the Kaggle dataset and start training.
3. After training, `final_model.h5` and `labels.json` will be saved. Download them.
4. Upload the model artifact to a cloud storage (S3/GCS) and set `MODEL_URL` in Render.
5. Push this repo to GitHub and create a Render Web Service (Docker) with `render.yaml` or via the Render UI.

---

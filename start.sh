#!/bin/bash
set -e

MODEL_DIR=/app/model
mkdir -p $MODEL_DIR

if [ -n "$MODEL_URL" ]; then
  echo "MODEL_URL provided. Downloading model..."
  MODEL_ARCHIVE="$MODEL_DIR/model_archive"
  if [ ! -f "$MODEL_DIR/model_ok" ]; then
    curl -L --retry 5 --retry-delay 5 -o "$MODEL_ARCHIVE" "$MODEL_URL"
    if file "$MODEL_ARCHIVE" | grep -q 'Zip archive'; then
      apt-get update && apt-get install -y unzip && unzip -o "$MODEL_ARCHIVE" -d "$MODEL_DIR"
    elif file "$MODEL_ARCHIVE" | grep -q 'gzip compressed'; then
      tar -xzf "$MODEL_ARCHIVE" -C "$MODEL_DIR"
    elif echo "$MODEL_ARCHIVE" | grep -E '\.h5$|\.hdf5$' >/dev/null 2>&1; then
      mv "$MODEL_ARCHIVE" "$MODEL_DIR/final_model.h5"
    else
      tar -xzf "$MODEL_ARCHIVE" -C "$MODEL_DIR" || true
      if [ ! -d "$MODEL_DIR/saved_model" ] && [ ! -f "$MODEL_DIR/final_model.h5" ]; then
        mv "$MODEL_ARCHIVE" "$MODEL_DIR/model_blob"
      fi
    fi
    touch "$MODEL_DIR/model_ok"
    echo "Model download/extract complete."
  else
    echo "Model already present. Skipping download."
  fi
else
  echo "No MODEL_URL provided; expecting model in /app/model"
fi

exec gunicorn -w 4 -b 0.0.0.0:8000 app_flask:app --timeout 120

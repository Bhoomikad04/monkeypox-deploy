#!/bin/bash
set -e
MODEL_DIR=/app/model
mkdir -p "$MODEL_DIR"

echo "MODEL_URL=${MODEL_URL:-<not set>}"

# Helper: download file to $MODEL_DIR/model_archive
download_to_archive() {
  out="$MODEL_DIR/model_archive"
  url="$1"
  echo "Downloading from: $url"

  # If it's a Google Drive "uc?export=download&id=..." link, handle the confirm token flow:
  if echo "$url" | grep -E "drive.google.com" >/dev/null 2>&1 ; then
    echo "Detected Google Drive URL — using token flow..."
    # extract file id if present
    fileid=$(echo "$url" | sed -n 's/.*id=\([^&]*\).*/\1/p')
    # fallback: try to extract /d/FILEID/ pattern
    if [ -z "$fileid" ]; then
      fileid=$(echo "$url" | sed -n 's#.*/d/\([^/]*\).*#\1#p')
    fi
    if [ -z "$fileid" ]; then
      echo "Could not extract file id from Google Drive URL. Attempting direct curl..."
      curl -L --retry 5 --retry-delay 5 -o "$out" "$url"
      return 0
    fi

    # First request to get confirm token and cookies
    curl -c /tmp/gd_cookies -s -L "https://drive.google.com/uc?export=download&id=${fileid}" > /tmp/gd_intermediate.html
    # Try to find confirm token
    confirm=$(sed -n 's/.*confirm=\([^&"]*\).*/\1/p' /tmp/gd_intermediate.html | head -n1 || true)
    if [ -z "$confirm" ]; then
      # try other pattern
      confirm=$(grep -o 'confirm=[0-9A-Za-z_-]*' /tmp/gd_intermediate.html 2>/dev/null | sed 's/confirm=//' | head -n1 || true)
    fi

    if [ -n "$confirm" ]; then
      echo "Using confirm token: $confirm"
      curl -Lb /tmp/gd_cookies -o "$out" "https://drive.google.com/uc?export=download&confirm=${confirm}&id=${fileid}"
    else
      # final fallback: try direct curl
      echo "No confirm token found; falling back to direct curl (may fail for large files)"
      curl -L --retry 5 --retry-delay 5 -o "$out" "$url"
    fi
  else
    # Non-Drive: plain curl
    curl -L --retry 5 --retry-delay 5 -o "$out" "$url"
  fi
}

# Download if model not present
if [ -n "$MODEL_URL" ] && [ ! -f "$MODEL_DIR/model_ok" ]; then
  download_to_archive "$MODEL_URL"

  # Try to detect archive type and extract
  if file "$MODEL_DIR/model_archive" | grep -q 'Zip archive'; then
    echo "Detected zip archive — extracting..."
    apt-get update && apt-get install -y unzip >/dev/null
    unzip -o "$MODEL_DIR/model_archive" -d "$MODEL_DIR"
  elif file "$MODEL_DIR/model_archive" | grep -q 'gzip compressed'; then
    echo "Detected gzip tar — extracting..."
    tar -xzf "$MODEL_DIR/model_archive" -C "$MODEL_DIR"
  elif echo "$MODEL_URL" | grep -E '\.h5$|\.hdf5$' >/dev/null 2>&1; then
    echo "Detected h5 file — moving into place..."
    mv "$MODEL_DIR/model_archive" "$MODEL_DIR/final_model.h5"
  else
    # attempt tar extraction, otherwise leave as-is
    tar -xzf "$MODEL_DIR/model_archive" -C "$MODEL_DIR" || mv "$MODEL_DIR/model_archive" "$MODEL_DIR/model_blob"
  fi

  touch "$MODEL_DIR/model_ok"
  echo "Model download/extract complete."
else
  echo "No MODEL_URL provided or model already present. Skipping download."
fi

# start gunicorn
echo "Starting gunicorn..."
exec gunicorn -w 4 -b 0.0.0.0:8000 app_flask:app --timeout 120

FROM python:3.12-slim

WORKDIR /app

# System deps for Pillow (avif), opencv-headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the shared layout package, the app, the logo assets and the root
# requirements (which installs template_build as an editable path).
COPY requirements.txt /app/requirements.txt
COPY template_build /app/template_build
COPY tme_editor_app /app/tme_editor_app
COPY assets /app/assets

RUN pip install --no-cache-dir -r /app/requirements.txt

EXPOSE 8501
CMD ["streamlit", "run", "/app/tme_editor_app/app.py", \
     "--server.port=8501", "--server.address=0.0.0.0", \
     "--server.headless=true"]

FROM python:3.12-slim

WORKDIR /app

# System deps for Pillow (avif), opencv-headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the two support packages (installed from local paths) and app
COPY template_build /app/template_build
COPY moore_build /app/moore_build
COPY tme_editor_app /app/tme_editor_app

RUN pip install --no-cache-dir -r /app/tme_editor_app/requirements.txt

EXPOSE 8501
CMD ["streamlit", "run", "/app/tme_editor_app/app.py", \
     "--server.port=8501", "--server.address=0.0.0.0", \
     "--server.headless=true"]

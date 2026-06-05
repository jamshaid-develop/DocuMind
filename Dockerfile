FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads faiss_index

ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=7860
ENV PYTHONUNBUFFERED=1

EXPOSE 7860

CMD ["python", "app.py"]
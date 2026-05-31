FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /converter

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py vectorize.py ./

CMD ["sh", "-c", "python main.py && python vectorize.py"]
FROM python:3.9-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libpq-dev \
    postgresql-client \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/static/uploads && \
    chmod -R 755 /app/static/uploads

ENV FLASK_APP=run.py
ENV FLASK_ENV=production

RUN if [ -f "init-db.sh" ]; then chmod +x init-db.sh; fi

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"]

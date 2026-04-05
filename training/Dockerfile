FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Create shared folders inside container
RUN mkdir -p /app/shared/data /app/shared/models

CMD ["python", "app.py"]
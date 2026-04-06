FROM python:3.11-slim


WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY app.py .


RUN mkdir -p /app/shared/data


CMD ["python", "app.py"]
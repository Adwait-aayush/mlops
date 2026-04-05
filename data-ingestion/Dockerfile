FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app.py .

# Create the shared folder inside the container
RUN mkdir -p /app/shared/data

# Run the script
CMD ["python", "app.py"]
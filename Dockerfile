FROM python:3.12.0a6-slim-buster

WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port the app runs on
EXPOSE 9500

# Run the application
CMD ["python3", "/app/app"]
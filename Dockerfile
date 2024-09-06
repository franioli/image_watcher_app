FROM python:3.11.9-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get -y install libgl1 libglib2.0-0

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port the app runs on
EXPOSE 9500

# Run the application
CMD ["python3", "/app/app"]
FROM python:3

# Set the working directory to the root
WORKDIR /

# Update apt and install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gnupg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install dependencies
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Copy the application code
COPY . /

# Expose the application's port
EXPOSE 8080

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]

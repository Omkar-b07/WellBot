# Use Python 3.10 as the base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the Flask app code
COPY . .

# Expose port 5000 (where Flask runs)
EXPOSE 5000

# Command to run the application
CMD ["python", "app.py"]
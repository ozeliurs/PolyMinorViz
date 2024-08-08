# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 8050

# Command to run the application using gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:8050", "main:app.server"]
FROM python:3.13-slim

WORKDIR /app

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Clone the repository
RUN git clone https://github.com/Lokesh-Chimakurthi/monte-carlo.git .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Gradio port
EXPOSE 7860

# Run the app
CMD ["python", "app.py"]

# Use the official Python image
FROM python:3.10-slim

# Install Chrome and dependencies
RUN apt-get update && \
    apt-get install -y wget gnupg2 unzip curl && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable=124.0.6367.91-1 && \
    rm -rf /var/lib/apt/lists/*

# Install ChromeDriver for Chrome 124
RUN wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/124.0.6367.91/chromedriver_linux64.zip" && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip && \
    chmod +x /usr/local/bin/chromedriver

# Set display port to avoid crash
ENV DISPLAY=:99

# Set workdir
WORKDIR /app

# Copy your code
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose Streamlit port
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]

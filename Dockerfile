# Use the official Python image
FROM python:3.10-slim

# Install Chrome and dependencies using modern approach
RUN apt-get update && \
    apt-get install -y wget gnupg2 unzip curl && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/googlechrome-linux-keyring.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/googlechrome-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# Set display port to avoid crash
ENV DISPLAY=:99
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROME_PATH=/usr/bin/google-chrome

# Set workdir
WORKDIR /app

# Copy your code
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose Streamlit port
EXPOSE 8501

# Set STREAMLIT_EMAIL
ENV STREAMLIT_EMAIL=""

# Set GOOGLE_API_KEY
ENV GOOGLE_API_KEY="AIzaSyC8UQjxTufYzbEFQxminUuR1I53P-MUspE"

# Create a non-root user for security
RUN useradd -m -s /bin/bash streamlit
USER streamlit

# Set workdir
WORKDIR /home/streamlit/app

# Copy requirements first for better caching
COPY --chown=streamlit:streamlit requirements.txt .

# Install Python dependencies
RUN pip install --user --upgrade pip
RUN pip install --user -r requirements.txt

# Copy your code
COPY --chown=streamlit:streamlit . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit with error handling (no email prompt flag)
CMD ["python", "-m", "streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=false"]

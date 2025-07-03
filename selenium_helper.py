import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@st.cache_resource
def setup_driver():
    """Setup Chrome driver with proper error handling"""
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_bin = os.environ.get('CHROME_BIN')
        if chrome_bin:
            chrome_options.binary_location = chrome_bin

        logger.info("Setting up ChromeDriver...")
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)
        driver.set_page_load_timeout(30)
        logger.info("ChromeDriver setup successful!")
        return driver
    except Exception as e:
        logger.error(f"Failed to setup ChromeDriver: {str(e)}")
        st.error(f"Failed to setup web driver: {str(e)}")
        return None

def get_driver():
    """Get or create Chrome driver instance"""
    try:
        driver = setup_driver()
        if driver is None:
            st.error("Could not initialize web driver")
            return None
        return driver
    except Exception as e:
        logger.error(f"Error getting driver: {str(e)}")
        st.error(f"Error getting driver: {str(e)}")
        return None

def safe_quit_driver(driver):
    """Safely quit the driver"""
    if driver:
        try:
            driver.quit()
            logger.info("Driver quit successfully")
        except Exception as e:
            logger.error(f"Error quitting driver: {str(e)}")

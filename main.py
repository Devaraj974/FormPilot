import streamlit as st
import tempfile
import os
import json
import time
import requests
# --- Streamlit Cloud: Ensure ChromeDriver is available ---
# import chromedriver_autoinstaller
# chromedriver_autoinstaller.install()

# --- Load .env for local development convenience ---
try:
    from dotenv import load_dotenv
    load_dotenv()
    dotenv_loaded = True
except ImportError:
    dotenv_loaded = False

# --- Existing Imports from main.py ---
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import requests
import re
from typing import Dict, Any
import PyPDF2
import google.generativeai as genai
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import fitz  # PyMuPDF for better link extraction
from urllib.parse import urlparse, urljoin
from langchain.tools import BaseTool

# --- LangGraph Imports ---
from langgraph.graph import StateGraph, END
from langchain.tools import Tool
from langchain_core.runnables import RunnableLambda

# --- Streamlit Page Config ---
st.set_page_config(
    page_title="AI Resume Form Filler",
    page_icon="📋",
    layout="wide"
)

# --- Sidebar Configuration ---
st.sidebar.header("⚙️ Configuration")
def_env_key = st.secrets["GOOGLE_API_KEY"] if "GOOGLE_API_KEY" in st.secrets else os.getenv("GOOGLE_API_KEY", "")
google_api_key = st.sidebar.text_input(
    "Google AI API Key",
    value=def_env_key,
    type="password"
)
if ("GOOGLE_API_KEY" in st.secrets and def_env_key):
    st.sidebar.info("Loaded API key from Streamlit secrets (hidden)")
if dotenv_loaded and not ("GOOGLE_API_KEY" in st.secrets) and def_env_key:
    st.sidebar.info("Loaded API key from .env file (hidden)")
headless_mode = st.sidebar.checkbox("Headless Browser", value=True)
timeout_seconds = st.sidebar.slider("Timeout (seconds)", 10, 60, 30)

if google_api_key:
    # Use Streamlit secrets if available, else fallback to environment variable
    if "GOOGLE_API_KEY" in st.secrets:
        os.environ['GOOGLE_API_KEY'] = st.secrets["GOOGLE_API_KEY"]
    else:
        os.environ['GOOGLE_API_KEY'] = google_api_key

# --- Session State Initialization ---
if 'extracted_data' not in st.session_state:
    st.session_state.extracted_data = None
if 'pdf_text' not in st.session_state:
    st.session_state.pdf_text = None
if 'form_url' not in st.session_state:
    st.session_state.form_url = ""
if 'submission_result' not in st.session_state:
    st.session_state.submission_result = None
if 'extracted_links' not in st.session_state:
    st.session_state.extracted_links = None


# CELL 1: Install Required Packages


# CELL 2: Import Libraries and Setup
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import os
import json
import requests
import re
from typing import Dict, Any

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time



# CELL 2.5: Enhanced PDF Link Extraction Class
import fitz  # PyMuPDF for better link extraction
from urllib.parse import urlparse, urljoin

class EnhancedPDFLinkExtractor:
    def __init__(self):
        self.driver = None
        self.setup_browser()

    def setup_browser(self):
        """Setup headless Chrome browser for link following"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")

            self.driver = webdriver.Chrome(options=chrome_options)
            print("✅ Browser setup completed")
        except Exception as e:
            print(f"⚠ Browser setup failed: {e}")
            self.driver = None

    def extract_links_from_pdf(self, pdf_path):
        """Extract clickable links directly from PDF file"""
        extracted_links = {}

        try:
            # Method 1: Using PyMuPDF (fitz) - better for link extraction
            pdf_document = fitz.open(pdf_path)
            all_links = []

            print(f"📄 Processing PDF with {pdf_document.page_count} pages...")

            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                links = page.get_links()

                for link in links:
                    if 'uri' in link:
                        url = link['uri']
                        if url and url.startswith(('http://', 'https://')):
                            all_links.append(url)
                            print(f"📎 Found link on page {page_num + 1}: {url}")

            pdf_document.close()

            # Remove duplicates
            unique_links = list(set(all_links))
            print(f"📊 Total unique links found: {len(unique_links)}")

            if unique_links:
                extracted_links = self.process_and_categorize_links(unique_links)
            else:
                print("❌ No clickable links found in PDF")
                # Fallback to text extraction method
                extracted_links = self.fallback_text_extraction(pdf_path)

            return extracted_links

        except Exception as e:
            print(f"❌ PDF link extraction failed: {e}")
            return self.fallback_text_extraction(pdf_path)

    def process_and_categorize_links(self, links):
        """Process links by following redirects and categorize them"""
        categorized_links = {}

        print("\n🔗 Processing and categorizing links...")

        for original_url in links:
            try:
                print(f"\n🔍 Processing: {original_url}")

                # Get final URL after redirects
                final_url = self.get_final_url(original_url)

                if final_url:
                    category = self.categorize_link(final_url)

                    if category:
                        categorized_links[category] = final_url
                        print(f"✅ {category.title()}: {final_url}")
                    else:
                        if 'portfolio' not in categorized_links:
                            categorized_links['portfolio'] = final_url
                            print(f"✅ Portfolio: {final_url}")

            except Exception as e:
                print(f"⚠ Error processing {original_url}: {e}")
                continue

        return categorized_links

    def get_final_url(self, url):
        """Follow redirects to get the final URL"""
        try:
            response = requests.head(url, allow_redirects=True, timeout=10)
            return response.url
        except:
            return self.get_final_url_with_browser(url)

    def get_final_url_with_browser(self, url):
        """Use browser to get final URL"""
        if not self.driver:
            return url

        try:
            self.driver.get(url)
            time.sleep(3)
            return self.driver.current_url
        except:
            return url

    def categorize_link(self, url):
        """Categorize a URL based on its domain"""
        url_lower = url.lower()

        if 'linkedin.com' in url_lower and ('/in/' in url_lower or '/profile/' in url_lower):
            return 'linkedin'
        elif 'github.com' in url_lower:
            return 'github'
        elif 'drive.google.com' in url_lower:
            return 'google_drive'
        elif 'dropbox.com' in url_lower:
            return 'dropbox'

        return None

    def fallback_text_extraction(self, pdf_path):
        """Fallback method using text extraction"""
        print("\n🔄 Falling back to text extraction method...")

        try:
            pdf_document = fitz.open(pdf_path)
            full_text = ""

            for page in pdf_document:
                full_text += page.get_text()

            pdf_document.close()
            return extract_links_from_text(full_text)

        except Exception as e:
            print(f"❌ Fallback text extraction failed: {e}")
            return {}

    def cleanup(self):
        """Clean up browser resources"""
        if self.driver:
            try:
                self.driver.quit()
                print("✅ Browser cleanup completed")
            except Exception as e:
                print(f"⚠ Browser cleanup failed: {e}")

# CELL 3: Simple Link Extraction Function
def extract_links_from_text(text):
    """Simple and effective link extraction"""
    links = {}

    # Clean text by adding spaces around URLs
    text = re.sub(r'([a-zA-Z])([www\.])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z])(https?://)', r'\1 \2', text)

    # Simple patterns for common links
    patterns = {
        'linkedin': [
            r'linkedin\.com/in/[\w\-\.%]+',
            r'https?://(?:www\.)?linkedin\.com/in/[\w\-\.%]+',
            r'linkedin:?\s*[\w\-\.%/]+',
        ],
        'github': [
            r'github\.com/[\w\-\.]+',
            r'https?://(?:www\.)?github\.com/[\w\-\.]+',
        ],
        'email': [
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        ]
    }

    for link_type, pattern_list in patterns.items():
        for pattern in pattern_list:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                url = matches[0]
                if link_type in ['linkedin', 'github'] and not url.startswith('http'):
                    url = 'https://' + url
                links[link_type] = url
                break

    return links

# CELL 3.5: Enhanced Link Extraction Function
def enhanced_extract_links_from_pdf(pdf_path):
    """Enhanced function to extract links from PDF"""

    print("🚀 Starting enhanced PDF link extraction...")

    extractor = EnhancedPDFLinkExtractor()

    try:
        extracted_links = extractor.extract_links_from_pdf(pdf_path)

        print(f"\n📊 Final extracted links summary:")
        if extracted_links:
            for link_type, url in extracted_links.items():
                print(f"   📎 {link_type.replace('_', ' ').title()}: {url}")
        else:
            print("   ❌ No links found")

        return extracted_links

    finally:
        extractor.cleanup()

# CELL 4: PDF Reader Tool
class PDFReaderTool(BaseTool):
    name: str = "PDF Reader"
    description: str = "Reads PDF files"

    def _run(self, pdf_path: str) -> str:
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"

# CELL 5: User Input Validation Function

# CELL 6: ENHANCED FORM FILLER CLASS - Replace the entire EnhancedWebFormFillerTool class in CELL 6
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from langchain.tools import BaseTool
from selenium.webdriver.support.ui import Select

class EnhancedWebFormFillerTool(BaseTool):
    name: str = "Enhanced Web Form Filler"
    description: str = "Fills web forms automatically with user input for missing fields"

    def _run(self, form_data: str, user_field_values: dict = None) -> str:
        logs = []
        try:
            logs.append("[START] EnhancedWebFormFillerTool._run")
            data = json.loads(form_data) if isinstance(form_data, str) else form_data
            form_url = data.get('form_url')
            logs.append(f"Form URL: {form_url}")
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
            driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
            try:
                logs.append("[STEP] Navigating to form URL...")
                driver.get(form_url)
                time.sleep(5)
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                logs.append("[STEP] Filling known fields...")
                filled_fields = self.fill_known_fields(driver, data)
                logs.append(f"Filled fields: {filled_fields}")
                logs.append("[STEP] Detecting unfilled fields...")
                unfilled_fields = self.detect_all_unfilled_fields(driver)
                logs.append(f"Unfilled fields: {[f['name'] for f in unfilled_fields]}")
                additional_filled = []
                if unfilled_fields:
                    logs.append("[STEP] Filling user-provided fields...")
                    if user_field_values:
                        additional_filled = self.fill_user_provided_fields(driver, user_field_values)
                        logs.append(f"User-provided fields filled: {additional_filled}")
                logs.append("[STEP] Checking form validation...")
                validation_errors = self.check_form_validation(driver)
                logs.append(f"Validation errors: {validation_errors}")
                total_filled = filled_fields + additional_filled
                logs.append("[STEP] Submitting the form...")
                submit_result = self.enhanced_form_submission_v2(driver, logs)
                logs.append(f"Submission result: {submit_result}")
                result = f"📋 FORM PROCESSING COMPLETE!\n"
                result += f"📊 Total fields filled: {len(total_filled)}\n"
                result += f"🎯 Fields: {', '.join(total_filled)}\n"
                result += f"\n{submit_result}\n"
                result += "\n[LOGS]\n" + "\n".join(logs)
                return result
            finally:
                driver.quit()
        except Exception as e:
            logs.append(f"❌ Error: {str(e)}")
            return f"❌ Error: {str(e)}\n[LOGS]\n" + "\n".join(logs)

    def fill_known_fields(self, driver, data):
        """Fill fields with known data from user input"""
        filled_fields = []

        # Field mappings with multiple selectors for each field type
        field_mappings = {
            'name': [
                "//input[@name='name' or @id='name']",
                "//input[contains(@placeholder, 'Name')]",
                "//input[contains(@name, 'first') or contains(@name, 'full')]",
                "//input[@type='text'][1]"
            ],
            'email': [
                "//input[@type='email']",
                "//input[@name='email' or @id='email']",
                "//input[contains(@placeholder, 'Email')]"
            ],
            'phone': [
                "//input[@type='tel']",
                "//input[@name='phone' or @id='phone' or @name='mobile']",
                "//input[contains(@placeholder, 'Phone') or contains(@placeholder, 'Mobile')]"
            ],
            'skills': [
                "//textarea[@name='skills' or @id='skills']",
                "//input[@name='skills' or @id='skills']",
                "//textarea[contains(@placeholder, 'Skills')]"
            ],
            'experience': [
                "//textarea[@name='experience' or @id='experience']",
                "//textarea[contains(@placeholder, 'Experience')]"
            ],
            'education': [
                "//textarea[@name='education' or @id='education']",
                "//input[@name='education' or @id='education']"
            ],
            'linkedin': [
                "//input[@name='linkedin' or @id='linkedin']",
                "//input[contains(@placeholder, 'LinkedIn')]"
            ],
            'github': [
                "//input[@name='github' or @id='github']",
                "//input[contains(@placeholder, 'GitHub')]"
            ],
            'address': [
                "//textarea[@name='address' or @id='address']",
                "//input[@name='address' or @id='address']"
            ]
        }

        print("\n📝 Filling known fields...")
        for field_name, selectors in field_mappings.items():
            field_value = data.get(field_name)

            if not field_value or field_value == "N/A":
                continue

            # Convert list to string if needed
            if isinstance(field_value, list):
                field_value = ', '.join(str(item) for item in field_value)

            # Try each selector until one works
            for selector in selectors:
                try:
                    element = WebDriverWait(driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    
                    if element.is_displayed() and element.is_enabled():
                        # Scroll to element and wait
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                        time.sleep(1)

                        # Clear and fill with enhanced method
                        self.safe_fill_field(driver, element, str(field_value))
                        
                        filled_fields.append(field_name)
                        print(f"   ✅ {field_name}: {str(field_value)[:50]}...")
                        break

                except:
                    continue

        return filled_fields

    def safe_fill_field(self, driver, element, value):
        """Safely fill a field with multiple fallback methods"""
        try:
            # Method 1: Clear and type normally
            element.clear()
            element.send_keys(value)
            time.sleep(0.5)
            
            # Verify the value was set
            if element.get_attribute('value') == value:
                return True
                
        except:
            pass
            
        try:
            # Method 2: JavaScript value setting
            driver.execute_script("arguments[0].value = arguments[1];", element, value)
            driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", element)
            driver.execute_script("arguments[0].dispatchEvent(new Event('change', {bubbles: true}));", element)
            time.sleep(0.5)
            return True
            
        except:
            pass
            
        try:
            # Method 3: Focus, clear, and type character by character
            element.click()
            element.clear()
            for char in value:
                element.send_keys(char)
                time.sleep(0.1)
            return True
            
        except:
            return False

    def detect_all_unfilled_fields(self, driver):
        """Detect all unfilled input fields on the page, including dropdowns and checkboxes"""
        unfilled_fields = []

        input_selectors = [
            "//input[@type='text']",
            "//input[@type='email']",
            "//input[@type='tel']",
            "//input[@type='url']",
            "//input[@type='number']",
            "//input[not(@type)]",
            "//textarea",
            # Do not include select here, handle separately
        ]

        print("\n🔍 Scanning for unfilled fields...")

        for selector in input_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)

                for element in elements:
                    if (element.is_displayed() and
                        element.is_enabled() and
                        not element.get_attribute('value') and
                        element.get_attribute('type') != 'hidden'):

                        field_info = {
                            'element': element,
                            'name': element.get_attribute('name') or element.get_attribute('id') or f"field_{len(unfilled_fields)+1}",
                            'placeholder': element.get_attribute('placeholder') or "No placeholder",
                            'type': element.get_attribute('type') or element.tag_name,
                            'required': element.get_attribute('required') is not None,
                            'label': self.get_field_label(driver, element)
                        }

                        unfilled_fields.append(field_info)

            except Exception as e:
                continue

        # Detect dropdowns (select)
        select_elements = driver.find_elements(By.TAG_NAME, "select")
        for element in select_elements:
            if element.is_displayed() and element.is_enabled() and not element.get_attribute('value'):
                options = [o.text for o in element.find_elements(By.TAG_NAME, "option") if o.text]
                field_info = {
                    'element': element,
                    'name': element.get_attribute('name') or element.get_attribute('id') or f"select_{len(unfilled_fields)+1}",
                    'type': 'select',
                    'options': options,
                    'label': self.get_field_label(driver, element),
                    'placeholder': element.get_attribute('placeholder') or "No placeholder",
                    'required': element.get_attribute('required') is not None,
                }
                unfilled_fields.append(field_info)

        # Detect checkboxes
        checkbox_elements = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
        for element in checkbox_elements:
            if element.is_displayed() and element.is_enabled() and not element.is_selected():
                field_info = {
                    'element': element,
                    'name': element.get_attribute('name') or element.get_attribute('id') or f"checkbox_{len(unfilled_fields)+1}",
                    'type': 'checkbox',
                    'label': self.get_field_label(driver, element),
                    'placeholder': element.get_attribute('placeholder') or "No placeholder",
                    'required': element.get_attribute('required') is not None,
                }
                unfilled_fields.append(field_info)

        return unfilled_fields

    def get_field_label(self, driver, element):
        """Try to find the label for a field"""
        try:
            element_id = element.get_attribute('id')
            if element_id:
                label = driver.find_element(By.XPATH, f"//label[@for='{element_id}']")
                if label.text.strip():
                    return label.text.strip()

            label = driver.execute_script("""
                var element = arguments[0];
                var prev = element.previousElementSibling;
                while(prev) {
                    if(prev.tagName.toLowerCase() === 'label') {
                        return prev.textContent.trim();
                    }
                    prev = prev.previousElementSibling;
                }
                return '';
            """, element)

            if label:
                return label

        except:
            pass

        return "No label found"

    def fill_user_provided_fields(self, driver, user_data):
        """Fill fields with user-provided data using robust selectors"""
        filled_fields = []
        for field_index, field_data in user_data.items():
            value = field_data['value']
            field_info = field_data['field_info']
            field_name = field_info.get('name', '')
            field_type = field_info.get('type', '')
            label_text = field_info.get('label', '')
            placeholder = field_info.get('placeholder', '')

            selectors = [
                f"//input[@name='{field_name}']",
                f"//input[@id='{field_name}']",
                f"//textarea[@name='{field_name}']",
                f"//textarea[@id='{field_name}']",
                f"//input[contains(@placeholder, '{placeholder}')]",
                f"//textarea[contains(@placeholder, '{placeholder}')]",
                f"//input[contains(@aria-label, '{label_text}')]",
                f"//textarea[contains(@aria-label, '{label_text}')]",
                f"//input[contains(@placeholder, '{label_text}')]",
                f"//textarea[contains(@placeholder, '{label_text}')]",
            ]
            element = None
            if field_type == 'select':
                try:
                    # Always re-find the element by name or id to avoid stale reference
                    if field_name:
                        try:
                            element = driver.find_element(By.NAME, field_name)
                        except:
                            try:
                                element = driver.find_element(By.ID, field_name)
                            except:
                                pass
                    if element is None:
                        # As a last resort, find the first visible select
                        selects = driver.find_elements(By.TAG_NAME, "select")
                        for sel in selects:
                            if sel.is_displayed() and sel.is_enabled():
                                element = sel
                                break
                    select = Select(element)
                    select.select_by_visible_text(value)
                    filled_fields.append(field_name)
                    print(f"   ✅ {field_name}: {value}")
                except Exception as e:
                    print(f"   ❌ Failed to select {value} for {field_name}: {e}")
            elif field_type == 'checkbox':
                try:
                    # Always re-find the element by name or id to avoid stale reference
                    if field_name:
                        try:
                            element = driver.find_element(By.NAME, field_name)
                        except:
                            try:
                                element = driver.find_element(By.ID, field_name)
                            except:
                                pass
                    if element is None:
                        # As a last resort, find the first visible checkbox
                        checkboxes = driver.find_elements(By.XPATH, "//input[@type='checkbox']")
                        for cb in checkboxes:
                            if cb.is_displayed() and cb.is_enabled():
                                element = cb
                                break
                    if value and not element.is_selected():
                        element.click()
                    elif not value and element.is_selected():
                        element.click()
                    filled_fields.append(field_name)
                except Exception as e:
                    print(f"   ❌ Failed to set checkbox {field_name}: {e}")
            else:
                # Existing logic for text/textarea
                for selector in selectors:
                    try:
                        element = driver.find_element(By.XPATH, selector)
                        break
                    except:
                        continue
                if element:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(1)
                    if self.safe_fill_field(driver, element, value):
                        filled_fields.append(field_name)
                        print(f"   ✅ {field_name}: {value}")
                    else:
                        print(f"   ❌ Failed to fill {field_name}")
                else:
                    print(f"   ❌ Failed to fill {field_name}: element not found")
        return filled_fields

    def check_form_validation(self, driver):
        """Check for validation errors"""
        errors = []

        error_selectors = [
            "//*[contains(@class, 'error') and text()]",
            "//*[contains(@class, 'invalid') and text()]",
            "//*[contains(@class, 'danger') and text()]",
            "//span[contains(@style, 'color: red') and text()]"
        ]

        for selector in error_selectors:
            try:
                error_elements = driver.find_elements(By.XPATH, selector)
                for element in error_elements:
                    if element.is_displayed() and element.text.strip():
                        errors.append(element.text.strip())
            except:
                continue

        return errors

    def enhanced_form_submission_v2(self, driver, logs=None):
        """Enhanced form submission with robust clicking mechanisms"""
        print("\n🚀 Starting enhanced form submission v2...")

        # Wait for any dynamic content to load
        time.sleep(3)

        # Store original URL for comparison
        original_url = driver.current_url
        print(f"📍 Original URL: {original_url}")

        # Find all potential submit elements
        submit_candidates = self.find_submit_candidates_v2(driver)

        if not submit_candidates:
            return "❌ No submit elements found on the page"

        print(f"🔍 Found {len(submit_candidates)} potential submit elements")

        # Try each candidate with multiple clicking strategies
        for i, candidate in enumerate(submit_candidates[:5], 1):  # Try top 5 candidates
            element = candidate['element']
            description = candidate['description']
            score = candidate['score']

            print(f"\n🎯 Attempt #{i}: {description} (score: {score})")

            # Try multiple clicking strategies for this element
            success = self.try_robust_click(driver, element, description)

            if success:
                # Wait and check if submission was successful
                time.sleep(5)

                # Check for URL change or success indicators
                verification_result = self.verify_submission_v2(driver, original_url)

                if "SUCCESS" in verification_result:
                    return verification_result
                elif "LIKELY" in verification_result:
                    return verification_result
                else:
                    print(f"   ⚠️ Click successful but no clear submission confirmation")
                    continue
            else:
                print(f"   ❌ All click methods failed for this element")
                continue

        # If no clear success, try form.submit() as last resort
        return self.try_form_submit_fallback(driver, original_url)

    def try_robust_click(self, driver, element, description):
        """Try multiple clicking strategies on an element"""
        click_strategies = [
            ("Standard Click", self.standard_click),
            ("JavaScript Click", self.javascript_click),
            ("ActionChains Click", self.action_chains_click),
            ("Forced Click", self.forced_click),
            ("Enter Key", self.enter_key_submit)
        ]

        for strategy_name, strategy_func in click_strategies:
            try:
                print(f"      🔄 Trying {strategy_name}...")

                # Scroll element into view
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(1)

                # Highlight element for debugging
                original_style = element.get_attribute('style')
                driver.execute_script("arguments[0].style.border='3px solid red'; arguments[0].style.backgroundColor='yellow';", element)
                time.sleep(0.5)

                # Try the click strategy
                success = strategy_func(driver, element)

                # Restore original style
                try:
                    driver.execute_script(f"arguments[0].style='{original_style or ''}';", element)
                except:
                    pass

                if success:
                    print(f"      ✅ {strategy_name} succeeded")
                    return True
                else:
                    print(f"      ❌ {strategy_name} failed")

            except Exception as e:
                print(f"      ❌ {strategy_name} exception: {e}")
                continue

        return False

    def standard_click(self, driver, element):
        """Standard click method"""
        try:
            element.click()
            return True
        except:
            return False

    def javascript_click(self, driver, element):
        """JavaScript click method"""
        try:
            driver.execute_script("arguments[0].click();", element)
            return True
        except:
            return False

    def action_chains_click(self, driver, element):
        """ActionChains click method"""
        try:
            webdriver.ActionChains(driver).move_to_element(element).click().perform()
            return True
        except:
            return False

    def forced_click(self, driver, element):
        """Forced click using JavaScript with event simulation"""
        try:
            # Dispatch multiple events
            driver.execute_script("""
                var element = arguments[0];
                var events = ['mousedown', 'mouseup', 'click'];
                events.forEach(function(eventType) {
                    var event = new MouseEvent(eventType, {
                        bubbles: true,
                        cancelable: true,
                        view: window
                    });
                    element.dispatchEvent(event);
                });
            """, element)
            return True
        except:
            return False

    def enter_key_submit(self, driver, element):
        """Try submitting by pressing Enter on the element"""
        try:
            element.send_keys(Keys.RETURN)
            return True
        except:
            return False

    def try_form_submit_fallback(self, driver, original_url):
        """Last resort: try form.submit() method"""
        print("\n🔄 Trying form.submit() as fallback...")

        try:
            forms = driver.find_elements(By.TAG_NAME, "form")

            if not forms:
                return "❌ No forms found for fallback submission"

            for i, form in enumerate(forms, 1):
                try:
                    print(f"   📋 Trying form #{i}")
                    driver.execute_script("arguments[0].submit();", form)
                    time.sleep(5)

                    # Check if submission worked
                    verification = self.verify_submission_v2(driver, original_url)
                    if "SUCCESS" in verification or "LIKELY" in verification:
                        return verification

                except Exception as e:
                    print(f"   ❌ Form #{i} submission failed: {e}")
                    continue

            return "❌ All form submission methods failed. Manual submission required."

        except Exception as e:
            return f"❌ Form submission fallback error: {e}"

    def find_submit_candidates_v2(self, driver):
        """Find potential submit elements on the page"""
        submit_candidates = []

        # Define potential submit elements
        submit_selectors = [
            "//button[@type='submit']",
            "//input[@type='submit']",
            "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]",
            "//input[@type='button' and contains(translate(@value, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit')]"
        ]

        for selector in submit_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        score = self.calculate_click_score(element)
                        submit_candidates.append({
                            'element': element,
                            'description': self.get_element_description(element),
                            'score': score
                        })
            except Exception as e:
                continue

        return submit_candidates

    def calculate_click_score(self, element):
        """Calculate a score for the clickability of an element"""
        score = 0
        if element.is_displayed() and element.is_enabled():
            score += 1
        if element.get_attribute('type') == 'submit':
            score += 1
        if element.get_attribute('type') == 'button':
            score += 0.5
        return score

    def get_element_description(self, element):
        """Get a human-readable description of an element"""
        tag_name = element.tag_name.upper()
        id_attr = element.get_attribute('id')
        name_attr = element.get_attribute('name')
        type_attr = element.get_attribute('type')
        text = element.text.strip()
        return f"{tag_name} ({id_attr or name_attr or type_attr}) - {text}"

    def verify_submission_v2(self, driver, original_url):
        """Enhanced verification of form submission with custom success check for AIGuruKul."""
        try:
            current_url = driver.current_url
            page_source = driver.page_source.lower()
            page_title = driver.title.lower()
            print(f"🔍 Verifying submission...")
            print(f"   Original URL: {original_url}")
            print(f"   Current URL: {current_url}")
            print(f"   Page Title: {driver.title}")
            # Check URL change
            url_changed = current_url != original_url
            # Success indicators
            success_indicators = [
                'thank you', 'success', 'submitted', 'received', 'confirmation',
                'thank-you', 'application submitted', 'form submitted',
                'congratulations', 'well done', 'complete', 'finished',
                'application received', 'we\'ll be in touch', 'hear from us'
            ]
            # Check various success signals
            url_success = any(indicator in current_url.lower() for indicator in 
                            ['success', 'complete', 'thank', 'confirmation', 'submitted'])
            content_success = any(indicator in page_source for indicator in success_indicators)
            title_success = any(indicator in page_title for indicator in success_indicators)
            # Look for success elements
            success_elements = driver.find_elements(By.XPATH,
                "//*[contains(@class, 'success') or contains(@class, 'confirmation') " +
                "or contains(@class, 'thank') or contains(text(), 'Thank you') " +
                "or contains(text(), 'Success') or contains(text(), 'submitted')]")
            element_success = len(success_elements) > 0
            # --- Custom check for AIGuruKul: is the submit button still present? ---
            submit_buttons = driver.find_elements(By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'submit application')]")
            submit_button_present = any(btn.is_displayed() for btn in submit_buttons)
            if not submit_button_present:
                return "🎉 FORM SUBMISSION SUCCESS! Confirmed by: Submit button disappeared after click."
            # Determine result
            if url_success or content_success or title_success or element_success:
                success_reasons = []
                if url_success: success_reasons.append("URL indicators")
                if content_success: success_reasons.append("success message")
                if title_success: success_reasons.append("title change")
                if element_success: success_reasons.append("success elements")
                return f"🎉 FORM SUBMISSION SUCCESS! Confirmed by: {', '.join(success_reasons)}"
            elif url_changed:
                return f"✅ LIKELY SUCCESS - Page redirected from form (URL changed)"
            else:
                # Check for form disappearance (another success indicator)
                forms = driver.find_elements(By.TAG_NAME, "form")
                if len(forms) == 0:
                    return f"✅ LIKELY SUCCESS - Form no longer present on page"
                return f"⚠ Form action completed but no clear success indicators found. Manual verification recommended."
        except Exception as e:
            return f"⚠ Submission verification failed: {e}"


# CELL 7: Interactive Form Completion Function
def complete_form_interactively(form_url, data):
    """Complete form with user interaction for missing fields"""

    print("\n🎯 INTERACTIVE FORM COMPLETION")
    print("=" * 40)
    print("This will:")
    print("1. Fill known fields automatically")
    print("2. Detect remaining empty fields")
    print("3. Ask you to fill missing fields")
    print("4. Submit the form")
    print("=" * 40)

    # Add form URL to data
    data['form_url'] = form_url

    # Use the parsed data as the default for the form
    editable_data = data.copy() if data else {}

    # Use enhanced form filler
    form_filler = EnhancedWebFormFillerTool()
    result = form_filler._run(json.dumps(data))


    return result



# CELL 8: FIXED AI Response Parsing Function
def parse_ai_response_safely(response_text):
    """
    Robustly extract and parse the first JSON object from the LLM response.
    If parsing fails, show the error and the raw response.
    """
    cleaned_response = response_text.strip()

    # Remove common markdown/code block markers
    cleaned_response = re.sub(r"^```json|^```|```$", "", cleaned_response, flags=re.MULTILINE).strip()

    # Try to parse the whole response as JSON
    try:
        return json.loads(cleaned_response)
    except Exception:
        pass

    # Try to extract the first JSON object from the text
    json_match = re.search(r'\\{[\\s\\S]*\\}', cleaned_response)
    if json_match:
        try:
            return json.loads(json_match.group())
        except Exception as e:
            print(f"⚠ JSON extraction failed: {e}")
            print(f"Raw response: {repr(cleaned_response[:200])}")

    # Final fallback: show error and return the raw response for manual correction
    print("⚠ Could not parse LLM response as JSON. Please check the raw response below.")
    print(cleaned_response)
    return {
        "name": "N/A",
        "email": "N/A",
        "phone": "N/A",
        "address": "N/A",
        "skills": [],
        "experience": [],
        "education": [],
        "linkedin": "N/A",
        "github": "N/A",
        "portfolio": "N/A",
        "google_drive": "N/A",
        "dropbox": "N/A",
        "raw_response": cleaned_response  # Add this so you can see/copy the real output
    }

# CELL 9: Updated Main Processing Function


# --- Streamlit Version of get_missing_details ---
def get_missing_details_streamlit(data):
    """Streamlit version of get_missing_details"""
    st.subheader("📝 Fill Missing Details")
    important_fields = {
        'name': 'Full Name',
        'email': 'Email Address',
        'phone': 'Phone Number',
        'linkedin': 'LinkedIn Profile URL',
        'github': 'GitHub Profile URL',
        'skills': 'Skills (comma-separated)',
        'address': 'Address/Location'
    }
    missing_fields = []
    for field, label in important_fields.items():
        current_value = data.get(field, 'N/A')
        if current_value in ['N/A', '', None] or (isinstance(current_value, list) and len(current_value) == 0):
            missing_fields.append(field)
    if missing_fields:
        st.warning(f"Missing fields detected: {', '.join(missing_fields)}")
        for field in missing_fields:
            new_value = st.text_input(f"Enter {field.replace('_', ' ').title()}:", key=f"missing_{field}")
            if new_value:
                if field == 'skills':
                    data[field] = [skill.strip() for skill in new_value.split(',')]
                else:
                    data[field] = new_value
    return data

# --- Main Streamlit App Structure ---
def main():
    st.title("🚀 AI Resume Form Filler")
    st.markdown("Upload your resume PDF and automatically fill job application forms")
    tab1, tab2, tab3 = st.tabs(["📤 Upload & Extract", "📝 Review Data", "🎯 Fill Form"])

    # --- Tab 1: Upload & Extract ---
    with tab1:
        st.header("Step 1: Upload Resume PDF and Extract Data")
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")
        form_url = st.text_input("Enter the form URL:", value=st.session_state.form_url)
        extract_button = st.button("Extract Data from PDF")
        if extract_button and uploaded_file and form_url:
            with st.spinner("Extracting data from PDF..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    temp_pdf_path = tmp_file.name
                st.session_state.form_url = form_url
                # Use existing PDFReaderTool
                pdf_reader = PDFReaderTool()
                pdf_text = pdf_reader._run(temp_pdf_path)
                st.session_state.pdf_text = pdf_text
                # Enhanced link extraction
                st.info("Extracting links from PDF...")
                extracted_links = enhanced_extract_links_from_pdf(temp_pdf_path)
                st.session_state.extracted_links = extracted_links
                # Use AI to extract structured data
                try:
                    # Always configure Gemini API with the latest key before model creation
                    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                    # Use the latest available model
                    model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
                except:
                    try:
                        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                        model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
                    except:
                        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                        model = genai.GenerativeModel('models/gemini-1.0-pro')
                
                prompt = f"""
                Extract information from this resume and return ONLY valid JSON without any markdown formatting or extra text.
                Resume Text:
                {pdf_text[:3000]}
                Extracted Links from PDF:
                {json.dumps(extracted_links, indent=2)}
                Return only this JSON structure with actual values:
                {{
                    "name": "Full Name",
                    "email": "email address",
                    "phone": "phone number",
                    "address": "full address or location",
                    "skills": ["skill1", "skill2"],
                    "experience": ["job description"],
                    "education": ["degree and institution"],
                    "linkedin": "linkedin url from extracted links",
                    "github": "github url from extracted links",
                    "portfolio": "portfolio url from extracted links",
                    "google_drive": "google drive url if found",
                    "dropbox": "dropbox url if found"
                }}
                IMPORTANT:
                - Return ONLY the JSON, no other text
                - Use the extracted links provided above - they are actual clickable URLs
                - Use "N/A" for missing info, empty arrays [] for missing lists
                - Do not wrap in markdown code blocks
                """
                st.info("Extracting data with AI...")
                try:
                    response = model.generate_content(prompt)
                    data = parse_ai_response_safely(response.text)
                except Exception as e:
                    error_msg = str(e)
                    if "API_KEY_INVALID" in error_msg or "API key expired" in error_msg:
                        st.error("❌ **Google Gemini API Key Error**\n\nYour API key is invalid or expired. Please:\n\n1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)\n2. Create a new API key\n3. Update the key in the sidebar\n\n**Error Details:** " + error_msg)
                    elif "quota" in error_msg.lower():
                        st.error("❌ **API Quota Exceeded**\n\nYou've reached the daily limit for the free Gemini API. Please:\n\n1. Wait 24 hours for quota reset, OR\n2. Create a new API key with a different Google account\n\n**Error Details:** " + error_msg)
                    elif "model" in error_msg.lower() or "generative" in error_msg.lower():
                        st.error("❌ **Model Error**\n\nThere's an issue with the AI model. Please try:\n\n1. Update the package: `pip install --upgrade google-generativeai`\n2. Restart your app\n3. Try again\n\n**Error Details:** " + error_msg)
                    else:
                        st.error(f"❌ **AI Extraction Failed**\n\nError: {error_msg}")
                    st.stop()
                # Enhance with extracted links
                for link_type, link_url in extracted_links.items():
                    if link_type in data:
                        data[link_type] = link_url
                st.session_state.extracted_data = data
                st.success("✅ Data extracted and saved! Proceed to the next tab.")
        elif extract_button:
            st.error("Please upload a PDF and enter the form URL.")

    # --- Tab 2: Review Data ---
    with tab2:
        st.header("Step 2: Review and Edit Extracted Data")
        if st.session_state.extracted_data:
            st.subheader("📋 Extracted Data")
            edited_data = {}
            for key, value in st.session_state.extracted_data.items():
                if isinstance(value, list):
                    edited_data[key] = st.text_area(f"{key.title()}:", value=", ".join(value) if value else "", key=f"edit_{key}")
                else:
                    edited_data[key] = st.text_input(f"{key.title()}:", value=value if value != "N/A" else "", key=f"edit_{key}")
            # Update session state with edited data
            if st.button("Save Edited Data"):
                for key, value in edited_data.items():
                    if key in ['skills', 'experience', 'education']:
                        st.session_state.extracted_data[key] = [v.strip() for v in value.split(',') if v.strip()]
                    else:
                        st.session_state.extracted_data[key] = value
                st.success("✅ Data updated!")
            # Download option
            st.download_button(
                "💾 Download Extracted Data",
                data=json.dumps(st.session_state.extracted_data, indent=2),
                file_name="extracted_resume_data.json",
                mime="application/json"
            )
        else:
            st.info("No data extracted yet. Please complete Step 1.")

    # --- Tab 3: Fill Form ---
    with tab3:
        st.header("Step 3: Fill and Submit the Form")
        if st.session_state.extracted_data and st.session_state.form_url:
            st.session_state.extracted_data = get_missing_details_streamlit(st.session_state.extracted_data)
            user_field_values = {}
            if 'awaiting_unfilled_fields' not in st.session_state:
                st.session_state['awaiting_unfilled_fields'] = False
            if 'logs' not in st.session_state:
                st.session_state['logs'] = []
            logs = st.session_state['logs']
            if st.session_state['awaiting_unfilled_fields']:
                unfilled_fields = st.session_state.get('unfilled_fields', [])
                with st.form("fill_unfilled_fields_form"):
                    for i, field in enumerate(unfilled_fields):
                        if field['type'] == 'select':
                            user_input = st.selectbox(f"{field['label']} ({field['name']})", field['options'], key=f"unfilled_{i}")
                        elif field['type'] == 'checkbox':
                            user_input = st.checkbox(f"{field['label']} ({field['name']})", key=f"unfilled_{i}")
                        else:
                            user_input = st.text_input(f"{field['label']} ({field['name']})", key=f"unfilled_{i}")
                        if user_input is not None:
                            user_field_values[i] = {
                                'value': user_input,
                                'field_info': field
                            }
                    submit_unfilled = st.form_submit_button("Submit Unfilled Fields and Fill Form")
                    if submit_unfilled:
                        with st.spinner("Filling and submitting the form..."):
                            try:
                                logs.append("📝 Filling user-provided data...")
                                chrome_options = Options()
                                chrome_options.add_argument("--headless=new")
                                chrome_options.add_argument("--no-sandbox")
                                chrome_options.add_argument("--disable-dev-shm-usage")
                                chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                                chrome_options.add_argument("--disable-web-security")
                                chrome_options.add_argument("--allow-running-insecure-content")
                                chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                                chrome_options.add_experimental_option('useAutomationExtension', False)
                                driver = webdriver.Chrome(options=chrome_options)
                                driver.get(st.session_state.form_url)
                                time.sleep(5)
                                WebDriverWait(driver, 10).until(
                                    lambda d: d.execute_script("return document.readyState") == "complete"
                                )
                                form_filler = EnhancedWebFormFillerTool()
                                logs.append("📝 Filling known fields...")
                                filled_fields = form_filler.fill_known_fields(driver, st.session_state.extracted_data)
                                for f in filled_fields:
                                    logs.append(f"   ✅ {f}: {st.session_state.extracted_data.get(f, '')}...")
                                additional_filled = form_filler.fill_user_provided_fields(driver, user_field_values)
                                for f in additional_filled:
                                    logs.append(f"   ✅ {f}: {user_field_values[[k for k,v in user_field_values.items() if v['field_info']['name']==f][0]]['value']}")
                                logs.append(f"✅ Filled {len(additional_filled)} additional fields")
                                logs.append("\n🚀 Starting enhanced form submission v2...")
                                submit_result = form_filler.enhanced_form_submission_v2(driver, logs)
                                driver.quit()
                                result = f"📋 FORM PROCESSING COMPLETE!\n"
                                result += f"📊 Total fields filled: {len(filled_fields) + len(additional_filled)}\n"
                                result += f"🎯 Fields: {', '.join(filled_fields + additional_filled)}\n"
                                result += f"\n{submit_result}"
                                st.session_state.submission_result = result
                                st.session_state['awaiting_unfilled_fields'] = False
                                st.success("Form submitted!")
                                st.code(result)
                                st.markdown("### Process Log")
                                st.code('\n'.join(logs))
                                st.download_button("Download Submission Report", data=result, file_name="submission_report.txt")
                                if "success" in result.lower():
                                    st.balloons()
                            except Exception as e:
                                st.error(f"Form submission failed: {e}")
                                st.expander("Debug Info").write(str(e))
            else:
                if st.button("Fill and Submit Form"):
                    with st.spinner("Filling and submitting the form..."):
                        try:
                            logs.clear()
                            logs.append("📝 Filling known fields...")
                            chrome_options = Options()
                            chrome_options.add_argument("--headless=new")
                            chrome_options.add_argument("--no-sandbox")
                            chrome_options.add_argument("--disable-dev-shm-usage")
                            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
                            chrome_options.add_argument("--disable-web-security")
                            chrome_options.add_argument("--allow-running-insecure-content")
                            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                            chrome_options.add_experimental_option('useAutomationExtension', False)
                            driver = webdriver.Chrome(options=chrome_options)
                            driver.get(st.session_state.form_url)
                            time.sleep(5)
                            WebDriverWait(driver, 10).until(
                                lambda d: d.execute_script("return document.readyState") == "complete"
                            )
                            form_filler = EnhancedWebFormFillerTool()
                            filled_fields = form_filler.fill_known_fields(driver, st.session_state.extracted_data)
                            for f in filled_fields:
                                logs.append(f"   ✅ {f}: {st.session_state.extracted_data.get(f, '')}...")
                            logs.append("\n🔍 Scanning for unfilled fields...")
                            unfilled_fields = form_filler.detect_all_unfilled_fields(driver)
                            logs.append(f"🔍 Found {len(unfilled_fields)} unfilled fields")
                            if unfilled_fields:
                                driver.quit()
                                st.session_state['unfilled_fields'] = unfilled_fields
                                st.session_state['awaiting_unfilled_fields'] = True
                                st.session_state['logs'] = logs
                                st.rerun()
                            else:
                                logs.append("\n🚀 Starting enhanced form submission v2...")
                                submit_result = form_filler.enhanced_form_submission_v2(driver, logs)
                                driver.quit()
                                result = f"📋 FORM PROCESSING COMPLETE!\n"
                                result += f"📊 Total fields filled: {len(filled_fields)}\n"
                                result += f"🎯 Fields: {', '.join(filled_fields)}\n"
                                result += f"\n{submit_result}"
                                st.session_state.submission_result = result
                                st.success("Form submitted!")
                                st.code(result)
                                st.markdown("### Process Log")
                                st.code('\n'.join(logs))
                                st.download_button("Download Submission Report", data=result, file_name="submission_report.txt")
                                if "success" in result.lower():
                                    st.balloons()
                        except Exception as e:
                            st.error(f"Form submission failed: {e}")
                            st.expander("Debug Info").write(str(e))
        else:
            st.info("Please extract and review data before filling the form.")
        if st.session_state.submission_result:
            st.subheader("📊 Submission Results")
            st.code(st.session_state.submission_result)
            if "success" in st.session_state.submission_result.lower():
                st.balloons()

# --- LangGraph Agent Integration ---
def run_langgraph_agent(pdf_path, form_url):
    """
    Orchestrate the workflow using LangGraph: 1) Read PDF, 2) Extract data, 3) Fill form.
    Returns the final result string.
    """
    # 1. Define tools as LangChain Tool objects
    pdf_reader_tool = Tool(
        name="PDF Reader",
        func=lambda path: PDFReaderTool()._run(path),
        description="Reads PDF files"
    )
    form_filler_tool = Tool(
        name="Form Filler",
        func=lambda data: EnhancedWebFormFillerTool()._run(json.dumps(data)),
        description="Fills web forms automatically with user input for missing fields"
    )
    # 2. Define LangGraph nodes
    def read_pdf_node(state):
        pdf_text = pdf_reader_tool.run(state["pdf_path"])
        return {**state, "pdf_text": pdf_text}
    def extract_data_node(state):
        # Use the same AI extraction logic as in the Streamlit workflow
        pdf_text = state["pdf_text"]
        form_url = state["form_url"]
        extracted_links = enhanced_extract_links_from_pdf(state["pdf_path"])
        try:
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
        except:
            try:
                genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                model = genai.GenerativeModel('models/gemini-1.5-flash-latest')
            except:
                genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
                model = genai.GenerativeModel('models/gemini-1.0-pro')
        prompt = f"""
        Extract information from this resume and return ONLY valid JSON without any markdown formatting or extra text.
        Resume Text:
        {pdf_text[:3000]}
        Extracted Links from PDF:
        {json.dumps(extracted_links, indent=2)}
        Return only this JSON structure with actual values:
        {{
            "name": "Full Name",
            "email": "email address",
            "phone": "phone number",
            "address": "full address or location",
            "skills": ["skill1", "skill2"],
            "experience": ["job description"],
            "education": ["degree and institution"],
            "linkedin": "linkedin url from extracted links",
            "github": "github url from extracted links",
            "portfolio": "portfolio url from extracted links",
            "google_drive": "google drive url if found",
            "dropbox": "dropbox url if found"
        }}
        IMPORTANT:
        - Return ONLY the JSON, no other text
        - Use the extracted links provided above - they are actual clickable URLs
        - Use "N/A" for missing info, empty arrays [] for missing lists
        - Do not wrap in markdown code blocks
        """
        try:
            response = model.generate_content(prompt)
            data = parse_ai_response_safely(response.text)
        except Exception as e:
            data = {"error": str(e)}
        # Enhance with extracted links
        for link_type, link_url in extracted_links.items():
            if link_type in data:
                data[link_type] = link_url
        return {**state, "extracted_data": data}
    def fill_form_node(state):
        # Use the form filler tool
        data = state["extracted_data"]
        data["form_url"] = state["form_url"]
        result = form_filler_tool.run(data)
        return {**state, "result": result}
    # 3. Build the LangGraph graph
    workflow = StateGraph()
    workflow.add_node("read_pdf", RunnableLambda(read_pdf_node))
    workflow.add_node("extract_data", RunnableLambda(extract_data_node))
    workflow.add_node("fill_form", RunnableLambda(fill_form_node))
    workflow.set_entry_point("read_pdf")
    workflow.add_edge("read_pdf", "extract_data")
    workflow.add_edge("extract_data", "fill_form")
    workflow.add_edge("fill_form", END)
    graph = workflow.compile()
    # 4. Run the agent
    initial_state = {"pdf_path": pdf_path, "form_url": form_url}
    final_state = graph.invoke(initial_state)
    return final_state.get("result", "No result from agent.")

if __name__ == "__main__":
    main()
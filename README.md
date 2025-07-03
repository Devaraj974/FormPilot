# AI Resume Form Filler

This app extracts information from your resume PDF and automatically fills job application forms using AI and browser automation.

## Features
- Upload your resume PDF
- Extracts structured data and links using Google Gemini AI
- Fills web forms automatically (including dropdowns and checkboxes)
- Handles missing fields with user prompts
- Works on Streamlit Cloud with multi-user support

## Requirements
- Python 3.8+
- All dependencies are listed in `requirements.txt`

## Streamlit Cloud Deployment Instructions

### 1. Fork or Upload the Repository
- Push your code (including `main.py`, `requirements.txt`, etc.) to GitHub.

### 2. Add Your Google Gemini API Key as a Secret
- In your Streamlit Cloud dashboard, go to your app > **Settings** > **Secrets**.
- Add:
  ```
  GOOGLE_API_KEY = your-google-gemini-api-key-here
  ```

### 3. Deploy the App
- Click **Deploy** in Streamlit Cloud.
- The app will automatically install all requirements, including ChromeDriver for Selenium.

### 4. Usage Notes
- The app uses headless Chrome and Selenium for browser automation.
- All users can upload their own PDF and fill forms independently.
- If you see errors about ChromeDriver or browser, make sure `chromedriver-autoinstaller` is in `requirements.txt` (it is by default).
- For local development, you can use a `.env` file for your API key, but on Streamlit Cloud, always use **Secrets**.

### 5. Troubleshooting
- If you hit API quota or key errors, update your Google Gemini API key in the secrets.
- For large PDFs or long-running forms, Streamlit Cloud may time out (try smaller files or faster forms).

## Credits
- Built with [Streamlit](https://streamlit.io/), [Selenium](https://www.selenium.dev/), [LangChain](https://python.langchain.com/), [LangGraph](https://langchain-ai.github.io/langgraph/), and [Google Generative AI](https://ai.google.dev/).

---

**Enjoy automated form filling!** 
# AI Resume Form Filler Agent

This app extracts information from your resume PDF and automatically fills job application forms using AI and browser automation.

## Features
- Upload your resume PDF
- Extracts structured data and links using Google Gemini AI
- Fills web forms automatically (including dropdowns and checkboxes)
- Handles missing fields with user prompts
- Deployable on Render.com with full browser automation support

## 🚀 How to Deploy on Render.com

Follow these steps to deploy this app on Render.com:

1. **Fork or Upload the Repository**
   - Push your code (including `main.py`, `requirements.txt`, `Dockerfile`, and `render.yaml`) to GitHub.

2. **Create a New Web Service on Render**
   - Go to [Render.com](https://dashboard.render.com/) and log in.
   - Click **"New +" → "Web Service"**.
   - Connect your GitHub repo and select your project.
   - Render will auto-detect your `Dockerfile` and use it to build the app.

3. **Set Environment Variables**
   - In the Render dashboard, add your Google Gemini API key as an environment variable:
     - Key: `GOOGLE_API_KEY`
     - Value: `your-google-gemini-api-key-here`

4. **Deploy and Access**
   - Click **"Create Web Service"**.
   - Wait for the build and deployment to finish.
   - Visit your Render URL to use your app!

**Live Demo:** [https://formpilot-k51d.onrender.com/](https://formpilot-k51d.onrender.com/)

## Requirements
- Python 3.8+
- All dependencies are listed in `requirements.txt`
- Google Chrome and ChromeDriver (handled automatically via Dockerfile)

## 🚀 Deployment on Render.com

### 1. Fork or Upload the Repository
- Push your code (including `main.py`, `requirements.txt`, `Dockerfile`, and `render.yaml`) to GitHub.

### 2. Create a Web Service on Render.com
- Go to [Render.com](https://dashboard.render.com/) and log in.
- Click **"New +" → "Web Service"**.
- Connect your GitHub repo and select your project.
- Render will auto-detect your `Dockerfile` and use it to build the app.

### 3. Set Environment Variables
- In the Render dashboard, add your Google Gemini API key as an environment variable:
  - Key: `GOOGLE_API_KEY`
  - Value: `your-google-gemini-api-key-here`

### 4. Deploy and Access
- Click **"Create Web Service"**.
- Wait for the build and deployment to finish.
- Visit your Render URL to use your app!

**Live Demo:** [https://formpilot-k51d.onrender.com/](https://formpilot-k51d.onrender.com/)

## 🐳 Local Development with Docker

1. Build the Docker image:
   ```
   docker build -t form-agent-langragh .
   ```
2. Run the app:
   ```
   docker run -p 8501:8501 -e GOOGLE_API_KEY=your-google-gemini-api-key-here form-agent-langragh
   ```
3. Open [http://localhost:8501](http://localhost:8501) in your browser.

## Troubleshooting
- If you see errors about Chrome or ChromeDriver, ensure you are using the provided Dockerfile.
- For API quota or key errors, update your Google Gemini API key in the Render dashboard.
- For large PDFs or long-running forms, Render's free plan may time out (try smaller files or upgrade your plan).

## Credits
- Built with [Streamlit](https://streamlit.io/), [Selenium](https://www.selenium.dev/), [LangChain](https://python.langchain.com/), [LangGraph](https://langchain-ai.github.io/langgraph/), and [Google Generative AI](https://ai.google.dev/).

---

**Enjoy automated form filling!** 

---

## License

This project is licensed under the [MIT License](LICENSE). 

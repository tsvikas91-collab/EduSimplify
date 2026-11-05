# EduSimplify – AI-Powered Course Content Simplification Agent

A Flask web application that accepts PDF, PPTX, and TXT course material or pasted text, then provides learning-level-aware simplification, summaries, key points, examples, or quizzes.

## Requirements
- Python 3.10+
- IBM Cloud account and a watsonx.ai project for live Granite responses

## Run locally (Windows)
Open this folder in VS Code, then run:

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in your browser.

## Connect IBM Granite
1. Create or open a project in IBM watsonx.ai and make sure a Granite chat model is available to that project.
2. Copy `.env.example` to a new file named `.env`.
3. Fill in `IBM_CLOUD_API_KEY`, `WATSONX_PROJECT_ID`, and `WATSONX_MODEL_ID`.
4. Set `WATSONX_URL` to your watsonx.ai region endpoint.
5. Stop and restart the Flask server.

Do not share your `.env` file or commit it to GitHub. The app uses IBM Cloud IAM to exchange the API key for an access token and then calls the watsonx.ai chat API.

## Demo mode
If IBM credentials are not configured, the app runs in Demo mode. It verifies upload and interface functionality but does not generate real AI simplifications. Configure IBM Granite for the actual AI functionality.

## Supported files
- PDF: selectable/extractable text. Scanned image-only PDFs need OCR, which is not included in this starter version.
- PowerPoint: `.pptx`
- Plain text: `.txt`

## Notes
- Maximum upload size: 15 MB.
- Extracted input is limited to 24,000 characters per request.
- Uploaded content is processed in memory and is not saved to a database.
- Treat AI output as study assistance and verify important academic details against the original notes.

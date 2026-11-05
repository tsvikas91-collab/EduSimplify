import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from pypdf import PdfReader
from pptx import Presentation
from services.ai_service import simplify_with_granite, granite_is_configured

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024  # 15 MB
ALLOWED_EXTENSIONS = {"pdf", "pptx", "txt"}
MAX_TEXT_CHARS = 24000

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text(file_storage, extension):
    if extension == "pdf":
        reader = PdfReader(file_storage)
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)
    if extension == "pptx":
        presentation = Presentation(file_storage)
        chunks = []
        for slide_number, slide in enumerate(presentation.slides, start=1):
            chunks.append(f"Slide {slide_number}")
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    chunks.append(shape.text.strip())
        return "\n".join(chunks)
    return file_storage.read().decode("utf-8", errors="replace")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/api/status")
def status():
    return jsonify({"granite_configured": granite_is_configured()})

@app.route("/api/simplify", methods=["POST"])
def simplify():
    uploaded = request.files.get("file")
    typed_text = request.form.get("text", "").strip()
    level = request.form.get("level", "Beginner")
    task = request.form.get("task", "Simplify")

    if level not in {"Beginner", "Intermediate", "Advanced", "Expert"}:
        return jsonify({"error": "Please select a valid learning level."}), 400
    if task not in {"Simplify", "Summarize", "Key points", "Examples", "Quiz"}:
        return jsonify({"error": "Please select a valid task."}), 400

    source_text = typed_text
    filename = "Pasted text"

    if uploaded and uploaded.filename:
        if not allowed_file(uploaded.filename):
            return jsonify({"error": "Upload a PDF, PPTX, or TXT file."}), 400
        filename = secure_filename(uploaded.filename)
        extension = filename.rsplit(".", 1)[1].lower()
        try:
            source_text = extract_text(uploaded.stream, extension).strip()
        except Exception as exc:
            return jsonify({"error": f"Could not read this file. Please check that it is a valid {extension.upper()} file."}), 400

    if not source_text:
        return jsonify({"error": "Upload a document or paste some course content first."}), 400

    source_text = source_text[:MAX_TEXT_CHARS]
    try:
        result = simplify_with_granite(source_text, level, task)
        return jsonify({
            "result": result,
            "filename": filename,
            "truncated": len(source_text) >= MAX_TEXT_CHARS,
            "mode": "IBM Granite" if granite_is_configured() else "Demo mode"
        })
    except Exception as exc:
        app.logger.exception("Simplification failed")
        return jsonify({"error": str(exc)}), 502

@app.errorhandler(413)
def too_large(_):
    return jsonify({"error": "File is too large. Maximum upload size is 15 MB."}), 413

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=True)

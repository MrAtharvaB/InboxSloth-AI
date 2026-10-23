import logging
import os
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory

from ai_service import AIService, AIServiceError
from validators import UploadValidationError, validate_upload


BASE_DIR = Path(__file__).resolve().parent


def create_app(test_config=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_mapping(
        MAX_CONTENT_LENGTH=1_048_576 + 8_192,
        OLLAMA_URL=os.getenv("OLLAMA_URL", "http://127.0.0.1:11434"),
        OLLAMA_MODEL=os.getenv("OLLAMA_MODEL", "gemma3:1b"),
        OLLAMA_TIMEOUT=float(os.getenv("OLLAMA_TIMEOUT", "90")),
        MAX_TEXT_CHARS=int(os.getenv("MAX_TEXT_CHARS", "120000")),
    )
    if test_config:
        app.config.update(test_config)

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("inboxsloth")
    ai_service = AIService(
        base_url=app.config["OLLAMA_URL"],
        model=app.config["OLLAMA_MODEL"],
        timeout=app.config["OLLAMA_TIMEOUT"],
        max_text_chars=app.config["MAX_TEXT_CHARS"],
    )
    app.extensions["ai_service"] = ai_service

    @app.get("/")
    def index():
        return render_template("index.html", model=app.config["OLLAMA_MODEL"])

    @app.get("/sample_chat.txt")
    def sample_chat():
        return send_from_directory(BASE_DIR, "sample_chat.txt", mimetype="text/plain")

    @app.get("/api/health")
    def health():
        status = ai_service.health()
        return jsonify(status), 200 if status["ollama_reachable"] else 503

    @app.post("/api/summarize")
    def summarize():
        uploaded = request.files.get("file")
        try:
            transcript = validate_upload(
                uploaded,
                max_bytes=1_048_576,
                max_chars=app.config["MAX_TEXT_CHARS"],
            )
            digest = ai_service.summarize(transcript)
            return jsonify({"digest": digest}), 200
        except UploadValidationError as error:
            return jsonify({"error": str(error), "code": error.code}), 400
        except AIServiceError as error:
            logger.warning("AI processing failed: %s", error)
            return jsonify({"error": str(error), "code": error.code}), error.status_code
        except Exception:
            logger.exception("Unexpected summarization failure")
            return jsonify(
                {
                    "error": "The digest could not be generated. Please try again.",
                    "code": "internal_error",
                }
            ), 500

    @app.errorhandler(413)
    def request_too_large(_error):
        return jsonify(
            {
                "error": "The file is too large. Upload a .txt file no larger than 1 MB.",
                "code": "file_too_large",
            }
        ), 413

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=False)

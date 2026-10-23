from io import BytesIO
from typing import Any


class UploadValidationError(Exception):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


def validate_upload(upload: Any, max_bytes: int, max_chars: int) -> str:
    if upload is None or not upload.filename:
        raise UploadValidationError("Choose a .txt chat export first.", "missing_file")
    if not upload.filename.lower().endswith(".txt"):
        raise UploadValidationError("Unsupported file type. Upload a .txt file.", "invalid_extension")

    stream = upload.stream
    stream.seek(0)
    content = stream.read(max_bytes + 1)
    if len(content) > max_bytes:
        raise UploadValidationError("The file is too large. Keep uploads under 1 MB.", "file_too_large")
    if not content:
        raise UploadValidationError("The selected file is empty.", "empty_file")
    try:
        text = BytesIO(content).read().decode("utf-8")
    except UnicodeDecodeError as error:
        raise UploadValidationError(
            "This file is not valid UTF-8 text. Export the chat as a plain-text UTF-8 file.",
            "invalid_encoding",
        ) from error
    if not text.strip():
        raise UploadValidationError("The selected file contains no useful text.", "empty_file")
    if len(text) > max_chars:
        raise UploadValidationError(
            f"This chat is too long to process. Keep it under {max_chars:,} characters.",
            "text_too_long",
        )
    return text

import os
import tempfile
import time

import clamd
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 700 * 1024 * 1024  # 100 MB
CLAMD_HOST = os.getenv("CLAMD_HOST", "clamav")
CLAMD_PORT = int(os.getenv("CLAMD_PORT", "3310"))


def is_mp4(file_stream):
    """Basic MP4/ISO-BMFF signature check: 'ftyp' normally starts at byte 4."""
    file_stream.seek(0)
    header = file_stream.read(12)
    file_stream.seek(0)
    return len(header) >= 8 and header[4:8] == b"ftyp"


def scan_with_clamav(file_stream):
    """Send the file as a stream to ClamAV; never execute or permanently save it."""
    last_error = None

    # ClamAV may need a short time to download its first signature database.
    for attempt in range(6):
        try:
            scanner = clamd.ClamdNetworkSocket(
                host=CLAMD_HOST, port=CLAMD_PORT, timeout=180
            )
            scanner.ping()
            file_stream.seek(0)
            result = scanner.instream(file_stream)
            status, detail = result["stream"]

            if status == "OK":
                return {"status": "clean", "detail": "No known malware signature detected."}
            if status == "FOUND":
                return {"status": "infected", "detail": detail}
            return {"status": "error", "detail": f"Unexpected scanner response: {status}"}

        except Exception as exc:
            last_error = str(exc)
            time.sleep(3)

    return {
        "status": "error",
        "detail": f"Could not connect to the antivirus engine: {last_error}",
    }


@app.get("/")
def home():
    return render_template("index.html")


@app.post("/api/scan")
def scan():
    uploaded = request.files.get("video")

    if not uploaded or not uploaded.filename:
        return jsonify(success=False, error="Please choose an MP4 file."), 400

    if not uploaded.filename.lower().endswith(".mp4"):
        return jsonify(success=False, error="Only .mp4 files are accepted."), 400

    # Use a temporary file so uploads are not retained in the project directory.
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp:
            temp_path = temp.name
            uploaded.save(temp)

        if os.path.getsize(temp_path) == 0:
            return jsonify(success=False, error="The uploaded file is empty."), 400

        with open(temp_path, "rb") as video:
            if not is_mp4(video):
                return jsonify(
                    success=False,
                    error="The file does not have a valid MP4/ISO-BMFF signature."
                ), 400

            result = scan_with_clamav(video)

        return jsonify(
            success=True,
            scan_status=result["status"],
            message=result["detail"],
            filename=os.path.basename(uploaded.filename),
        )

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@app.errorhandler(413)
def too_large(_error):
    return jsonify(success=False, error="File is too large. Maximum size is 100 MB."), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)

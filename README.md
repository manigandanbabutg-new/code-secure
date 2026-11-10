# MP4 Shield — MP4 Malware Scanner

A Flask website that validates an uploaded MP4 file and streams it to ClamAV for signature-based malware scanning.

## Features
- MP4 extension and basic `ftyp` signature validation
- 100 MB upload limit
- ClamAV scanning through its network daemon
- Clean / infected / scan-error result states
- Temporary file is deleted after scanning
- Docker Compose setup for the website and antivirus engine

## Run with Docker (recommended)

Install Docker Desktop, open a terminal in this folder, then run:

```bash
docker compose up --build
```

The first startup can take a few minutes because ClamAV needs to download its malware signature database.

Open: http://localhost:8000

To stop:

```bash
docker compose down
```

## Run locally (advanced)

You need Python 3.12+ and a reachable ClamAV daemon listening on TCP port 3310.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

Set `CLAMD_HOST` and `CLAMD_PORT` if your ClamAV daemon is not at `localhost:3310`.

## API

`POST /api/scan`

Send multipart form data with the file field named `video`.

Example response:

```json
{
  "success": true,
  "scan_status": "clean",
  "message": "No known malware signature detected.",
  "filename": "sample.mp4"
}
```

Possible `scan_status` values: `clean`, `infected`, `error`.

## Important security limitations

- A clean scan means ClamAV did not find a signature it recognizes; it is not a guarantee that the file is safe.
- Signature scanning does not prove that an MP4 is structurally safe or free from unknown exploits.
- The `ftyp` check is only a basic format check, not full media-file validation.
- For production, add authentication, rate limiting, HTTPS, request timeouts, monitoring, and isolated resource limits. Keep ClamAV signatures updated.
- Do not automatically play uploaded files or serve them back to users.

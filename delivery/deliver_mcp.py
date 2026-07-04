import os
import json
import base64
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from mcp.server.fastmcp import FastMCP
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ─── CONFIG ───────────────────────────────────────────────────────────────────

# Scopes needed — Drive file creation + Gmail send only
SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/gmail.send"
]

# Paths — relative to project root (run this script from marketing_agent/)
PROJECT_ROOT = Path(__file__).parent.parent
CREDENTIALS_FILE = PROJECT_ROOT / "credentials.json"
TOKEN_FILE = PROJECT_ROOT / "token.json"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# ─── OAUTH HELPER ─────────────────────────────────────────────────────────────

def get_google_services():
    """
    Handles OAuth2 flow. On first run opens a browser for consent.
    On subsequent runs uses token.json silently.
    Returns (drive_service, gmail_service).
    """
    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {CREDENTIALS_FILE}. "
                    "Download it from Google Cloud Console > APIs & Services > Credentials."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            creds = flow.run_local_server(port=0)

        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    drive_service = build("drive", "v3", credentials=creds)
    gmail_service = build("gmail", "v1", credentials=creds)
    return drive_service, gmail_service


# ─── FASTMCP SERVER ───────────────────────────────────────────────────────────

mcp = FastMCP("marketing-delivery")


@mcp.tool()
def upload_session_to_drive(session_id: str) -> dict:
    """
    Reads all output files from outputs/session_{id}/ and uploads them
    to a new Google Drive folder named after the session.
    Returns the Drive folder URL.
    """
    session_dir = OUTPUTS_DIR / f"session_{session_id}"

    if not session_dir.exists():
        return {
            "success": False,
            "error": f"Session folder not found: {session_dir}"
        }

    # Collect all files to upload
    files_to_upload = list(session_dir.rglob("*"))
    files_to_upload = [f for f in files_to_upload if f.is_file()]

    if not files_to_upload:
        return {
            "success": False,
            "error": f"No files found in {session_dir}"
        }

    drive_service, _ = get_google_services()

    # Create a folder on Drive
    folder_name = f"Marketing Agent — Session {session_id[:8]}"
    folder_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder"
    }
    folder = drive_service.files().create(
        body=folder_metadata,
        fields="id, webViewLink"
    ).execute()

    folder_id = folder["id"]
    folder_url = folder["webViewLink"]

    # Upload each file into the folder
    uploaded = []
    failed = []

    for file_path in files_to_upload:
        try:
            # Determine MIME type
            suffix = file_path.suffix.lower()
            mime_map = {
                ".md":   "text/markdown",
                ".json": "application/json",
                ".txt":  "text/plain",
                ".jpg":  "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png":  "image/png",
                ".pdf":  "application/pdf",
            }
            mime_type = mime_map.get(suffix, "application/octet-stream")

            file_metadata = {
                "name": file_path.name,
                "parents": [folder_id]
            }
            media = MediaFileUpload(str(file_path), mimetype=mime_type)

            drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id, name"
            ).execute()

            uploaded.append(file_path.name)

        except Exception as e:
            failed.append({"file": file_path.name, "error": str(e)})

    # Make folder shareable via link
    drive_service.permissions().create(
        fileId=folder_id,
        body={"type": "anyone", "role": "reader"}
    ).execute()

    return {
        "success": True,
        "folder_name": folder_name,
        "folder_url": folder_url,
        "files_uploaded": uploaded,
        "files_failed": failed,
        "total_uploaded": len(uploaded)
    }


@mcp.tool()
def email_session_summary(session_id: str, recipient_email: str) -> dict:
    """
    Sends a delivery email to recipient_email with a summary of what
    was generated and a link to the Drive folder (if already uploaded).
    Call upload_session_to_drive first to get the folder URL.
    """
    session_dir = OUTPUTS_DIR / f"session_{session_id}"

    if not session_dir.exists():
        return {
            "success": False,
            "error": f"Session folder not found: {session_dir}"
        }

    # Read available output files to build summary
    output_files = [f.name for f in session_dir.rglob("*") if f.is_file()]

    # Try to read eval score if it exists
    eval_score = "Pending"
    eval_path = session_dir / "eval.json"
    if eval_path.exists():
        try:
            with open(eval_path) as f:
                eval_data = json.load(f)
                score = eval_data.get("grand_total", "")
                max_score = eval_data.get("max_possible", 38)
                if score:
                    eval_score = f"{score} / {max_score}"
        except Exception:
            pass

    # Try to read business name from intake brief
    business_name = "Your Business"
    intake_path = session_dir / "intake_brief.json"
    if intake_path.exists():
        try:
            with open(intake_path) as f:
                intake = json.load(f)
                business_name = intake.get("business_name", "Your Business")
        except Exception:
            pass

    # Build email HTML
    files_list = "".join(f"<li>{f}</li>" for f in output_files)

    html_body = f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <h2 style="color: #1a73e8;">Your Marketing Strategy is Ready</h2>
      <p>Hi,</p>
      <p>Your full-funnel marketing strategy for <strong>{business_name}</strong>
      has been generated and is ready for review.</p>

      <h3 style="color: #333;">What's included:</h3>
      <ul>{files_list}</ul>

      <h3 style="color: #333;">Evaluation Score:</h3>
      <p style="font-size: 18px; color: #1a73e8;"><strong>{eval_score} points</strong></p>

      <h3 style="color: #333;">Next Steps:</h3>
      <ol>
        <li>Review the SEO strategy and keyword clusters</li>
        <li>Import the Google Ads keywords into Google Ads Editor</li>
        <li>Upload Meta ad copy to Meta Ads Manager</li>
        <li>Add JSON-LD schema markup to your website pages</li>
      </ol>

      <p style="color: #666; font-size: 12px; margin-top: 40px;">
        Generated by Full-Funnel Marketing Agent |
        Session: {session_id[:8]}
      </p>
    </body></html>
    """

    # Build plain text fallback
    plain_body = f"""
Your Marketing Strategy is Ready

Business: {business_name}
Session: {session_id[:8]}
Evaluation Score: {eval_score}

Files generated:
{chr(10).join("- " + f for f in output_files)}

Next steps:
1. Review the SEO strategy and keyword clusters
2. Import Google Ads keywords into Google Ads Editor
3. Upload Meta ad copy to Meta Ads Manager
4. Add JSON-LD schema markup to your website pages
    """.strip()

    # Build the MIME message
    message = MIMEMultipart("alternative")
    message["Subject"] = f"Your Marketing Strategy is Ready — {business_name}"
    message["From"] = "me"
    message["To"] = recipient_email

    message.attach(MIMEText(plain_body, "plain"))
    message.attach(MIMEText(html_body, "html"))

    # Encode and send via Gmail API
    try:
        _, gmail_service = get_google_services()

        raw = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode("utf-8")

        gmail_service.users().messages().send(
            userId="me",
            body={"raw": raw}
        ).execute()

        return {
            "success": True,
            "sent_to": recipient_email,
            "subject": f"Your Marketing Strategy is Ready — {business_name}",
            "files_mentioned": output_files,
            "eval_score": eval_score
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Starting Marketing Delivery MCP Server...")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Outputs directory: {OUTPUTS_DIR}")
    print("Tools available: upload_session_to_drive, email_session_summary")
    mcp.run()
"""
gmail_ops.py
Low-level Gmail operations via the Gmail API. No AI here - pure API calls.
All functions are zero-cost against your Gemini quota (Gmail API has its
own separate, very generous free quota).
"""

import base64
from email.mime.text import MIMEText
import gmail_auth


def _get_header(headers, name):
    for h in headers:
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def list_messages(query="", max_results=10):
    """
    Search/list messages using Gmail search syntax, e.g.:
      "is:unread"
      "from:boss@company.com"
      "subject:invoice after:2026/08/01"
    Returns list of dicts: {id, subject, from, date, snippet}
    """
    service = gmail_auth.get_gmail_service()
    result = service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    messages = result.get("messages", [])

    output = []
    for msg in messages:
        full = service.users().messages().get(userId="me", id=msg["id"], format="metadata",
                                                metadataHeaders=["Subject", "From", "Date"]).execute()
        headers = full.get("payload", {}).get("headers", [])
        output.append({
            "id": msg["id"],
            "subject": _get_header(headers, "Subject"),
            "from": _get_header(headers, "From"),
            "date": _get_header(headers, "Date"),
            "snippet": full.get("snippet", "")
        })

    return output


def get_message_body(message_id):
    """Fetches the full plain-text body of a specific message."""
    service = gmail_auth.get_gmail_service()
    msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()

    payload = msg.get("payload", {})
    body = _extract_plain_text(payload)
    headers = payload.get("headers", [])

    return {
        "id": message_id,
        "subject": _get_header(headers, "Subject"),
        "from": _get_header(headers, "From"),
        "date": _get_header(headers, "Date"),
        "body": body
    }


def _extract_plain_text(payload):
    """Recursively walks the MIME payload to find text/plain content."""
    if payload.get("mimeType") == "text/plain" and "data" in payload.get("body", {}):
        data = payload["body"]["data"]
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    for part in payload.get("parts", []):
        text = _extract_plain_text(part)
        if text:
            return text

    return ""


def get_unread_count():
    service = gmail_auth.get_gmail_service()
    result = service.users().messages().list(userId="me", q="is:unread", maxResults=1).execute()
    return result.get("resultSizeEstimate", 0)


def send_message(to, subject, body, cc=None):
    """
    Sends an email. Returns the sent message id on success.
    This is a REAL send - your router should confirm with the user before
    calling this, and config.LIVE_SEND_ENABLED gates it as an extra safety net.
    """
    import config
    if not config.LIVE_SEND_ENABLED:
        raise PermissionError(
            "LIVE_SEND_ENABLED is False in config.py. Set it to True only "
            "when you're ready for real emails to actually be sent."
        )

    service = gmail_auth.get_gmail_service()

    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    if cc:
        message["cc"] = cc

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    sent = service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return sent.get("id")


def mark_as_read(message_id):
    service = gmail_auth.get_gmail_service()
    service.users().messages().modify(
        userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
    ).execute()


def archive_message(message_id):
    service = gmail_auth.get_gmail_service()
    service.users().messages().modify(
        userId="me", id=message_id, body={"removeLabelIds": ["INBOX"]}
    ).execute()


def extract_attachments(message_id, save_dir=None):
    """Downloads and extracts all attachments for a specific message id."""
    import os
    save_path = save_dir or os.path.join(os.path.dirname(__file__), "data", "attachments", message_id)
    os.makedirs(save_path, exist_ok=True)

    try:
        service = gmail_auth.get_gmail_service()
        msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
        payload = msg.get("payload", {})
        saved_files = []

        def _process_parts(parts):
            for part in parts:
                filename = part.get("filename")
                body = part.get("body", {})
                att_id = body.get("attachmentId")
                if filename and att_id:
                    att = service.users().messages().attachments().get(
                        userId="me", messageId=message_id, id=att_id
                    ).execute()
                    file_data = base64.urlsafe_b64decode(att.get("data", "").encode("UTF-8"))
                    out_file = os.path.join(save_path, filename)
                    with open(out_file, "wb") as f:
                        f.write(file_data)
                    saved_files.append({"filename": filename, "path": out_file, "size_bytes": len(file_data)})
                if "parts" in part:
                    _process_parts(part["parts"])

        if "parts" in payload:
            _process_parts(payload["parts"])

        return {"message_id": message_id, "saved_directory": save_path, "attachments": saved_files}
    except Exception as e:
        return {"message_id": message_id, "error": str(e), "attachments": []}


def list_important_messages(max_results=10):
    """Fetches high-priority / starred / important emails."""
    return list_messages("is:important OR is:starred", max_results)


def search_by_category(category_keyword, max_results=10):
    """Searches messages matching specialized keywords (invoices, jobs, college, clients)."""
    return list_messages(category_keyword, max_results)


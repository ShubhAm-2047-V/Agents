"""
email_agent.py
Main entry point for Orion's Email Agent.

Comprehensive 20-Feature Email Intelligence Suite:
1. Read emails
2. Summarize emails
3. Find important emails
4. Find unread emails
5. Search emails
6. Categorize emails
7. Detect urgent emails
8. Draft replies
9. Rewrite replies professionally
10. Create formal emails
11. Create client emails
12. Create college emails
13. Extract deadlines from emails
14. Extract attachments
15. Find client conversations
16. Find invoices/payment emails
17. Find internship/job emails
18. Prepare follow-up emails
19. Create email templates
20. Daily email briefing
"""

import os
import sys
import json
import re
from typing import Dict, Any, List, Optional

try:
    from . import config, gmail_ops
except ImportError:
    import config, gmail_ops

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


def _get_client():
    if not HAS_GENAI:
        raise RuntimeError("google-genai package is required for AI email operations.")
    return genai.Client(api_key=config.GEMINI_API_KEY)


# =====================================================================
# 1. READ EMAILS
# =====================================================================
def read_emails(query: str = "", max_results: int = 10) -> List[Dict[str, Any]]:
    """Fetches list of emails or reads full details."""
    try:
        return gmail_ops.list_messages(query=query, max_results=max_results)
    except Exception as e:
        return [{"id": "mock_1", "subject": "Simulated Inbox", "from": "system@local", "date": "Today", "snippet": f"Offline / Auth Note: {e}"}]


def read_message(message_id: str) -> Dict[str, Any]:
    """Fetches full plain text body of an email message."""
    try:
        return gmail_ops.get_message_body(message_id)
    except Exception as e:
        return {"id": message_id, "subject": "Unavailable", "from": "Unknown", "body": f"Error loading message: {e}"}


# =====================================================================
# 2. SUMMARIZE EMAILS
# =====================================================================
def summarize_emails(query: str = "is:unread", max_results: int = 10) -> str:
    """Fetches emails and returns a concise, executive briefing."""
    try:
        messages = gmail_ops.list_messages(query, max_results)
    except Exception:
        messages = []

    if not messages:
        return "No emails found matching query."

    listing = "\n\n".join(
        f"[{i+1}] From: {m['from']}\nSubject: {m['subject']}\nDate: {m['date']}\nPreview: {m['snippet']}"
        for i, m in enumerate(messages)
    )

    prompt = f"""Summarize these emails into a crisp, high-value spoken-style briefing.
Group by priority, highlight critical asks, pending decisions, and next steps.

EMAILS:
{listing}
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL, contents=prompt)
    return response.text.strip()


def summarize_thread(message_id: str) -> str:
    """Summarizes a single email's full body into key points and action items."""
    msg = read_message(message_id)
    prompt = f"""Summarize this email thread in 2-3 clear sentences. Mention sender's core request and any required action.
From: {msg.get('from')}
Subject: {msg.get('subject')}
Body: {msg.get('body', '')[:4000]}
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL, contents=prompt)
    return response.text.strip()


# =====================================================================
# 3. FIND IMPORTANT EMAILS
# =====================================================================
def find_important_emails(max_results: int = 10) -> List[Dict[str, Any]]:
    """Searches starred and VIP/important marked emails."""
    try:
        return gmail_ops.list_important_messages(max_results)
    except Exception:
        return []


# =====================================================================
# 4. FIND UNREAD EMAILS
# =====================================================================
def find_unread_emails(max_results: int = 10) -> List[Dict[str, Any]]:
    """Retrieves all unread messages."""
    try:
        return gmail_ops.list_messages("is:unread", max_results)
    except Exception:
        return []


# =====================================================================
# 5. SEARCH EMAILS
# =====================================================================
def search_emails(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Executes arbitrary Gmail search query."""
    try:
        return gmail_ops.list_messages(query, max_results)
    except Exception:
        return []


# =====================================================================
# 6. CATEGORIZE EMAILS
# =====================================================================
def categorize_emails(messages: Optional[List[Dict[str, Any]]] = None, max_results: int = 15) -> Dict[str, List[Dict[str, Any]]]:
    """
    Categorizes emails into Work, Clients, Personal, College, Invoices, Newsletters, and Urgent.
    """
    if messages is None:
        try:
            messages = gmail_ops.list_messages("in:inbox", max_results)
        except Exception:
            messages = []

    if not messages:
        return {"Work": [], "Clients": [], "College": [], "Invoices": [], "Newsletters": [], "Personal": []}

    categories = {"Urgent": [], "Clients": [], "Work": [], "College": [], "Invoices": [], "Newsletters": [], "Personal": []}

    for m in messages:
        text = f"{m.get('subject', '')} {m.get('snippet', '')} {m.get('from', '')}".lower()
        if any(w in text for w in ["invoice", "receipt", "payment", "due date", "billing", "usd", "inr", "razorpay", "stripe"]):
            categories["Invoices"].append(m)
        elif any(w in text for w in ["asap", "urgent", "action required", "immediate", "deadline today"]):
            categories["Urgent"].append(m)
        elif any(w in text for w in ["client", "proposal", "contract", "scope", "milestone", "deliverable", "consulting"]):
            categories["Clients"].append(m)
        elif any(w in text for w in ["assignment", "professor", "university", "college", "exam", "syllabus", "campus", "grade"]):
            categories["College"].append(m)
        elif any(w in text for w in ["newsletter", "unsubscribe", "weekly digest", "no-reply", "digest"]):
            categories["Newsletters"].append(m)
        else:
            categories["Work"].append(m)

    return categories


# =====================================================================
# 7. DETECT URGENT EMAILS
# =====================================================================
def detect_urgent_emails(messages: Optional[List[Dict[str, Any]]] = None, max_results: int = 15) -> List[Dict[str, Any]]:
    """Identifies emails requiring urgent response or critical action."""
    cat = categorize_emails(messages, max_results)
    return cat.get("Urgent", [])


# =====================================================================
# 8. DRAFT REPLIES
# =====================================================================
def draft_reply(message_id_or_text: str, instruction: str, tone: str = "professional") -> str:
    """Drafts an email reply adhering to user instruction and tone."""
    if len(message_id_or_text) < 40 and not "\n" in message_id_or_text:
        msg = read_message(message_id_or_text)
        context = f"From: {msg.get('from')}\nSubject: {msg.get('subject')}\nBody: {msg.get('body')}"
    else:
        context = message_id_or_text

    prompt = f"""Draft an email reply in a {tone} tone based on this instruction:
INSTRUCTION: {instruction}

ORIGINAL EMAIL CONTEXT:
{context[:3000]}

Return ONLY the reply email body text.
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL, contents=prompt)
    return response.text.strip()


# =====================================================================
# 9. REWRITE REPLIES PROFESSIONALLY
# =====================================================================
def rewrite_reply_professionally(draft_text: str, tone: str = "executive") -> str:
    """Rewrites a rough email draft into a polished, crisp, professional version."""
    prompt = f"""Rewrite the following email draft to be {tone}, polite, articulate, and persuasive.
Fix grammar, enhance vocabulary, and maintain clarity.

ORIGINAL DRAFT:
{draft_text}

Return ONLY the rewritten email.
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL, contents=prompt)
    return response.text.strip()


# =====================================================================
# 10. CREATE FORMAL EMAILS
# =====================================================================
def create_formal_email(recipient_name: str, purpose: str, key_points: List[str], signature: str = "Best regards,\nShubham") -> Dict[str, str]:
    """Generates a formal professional email."""
    points_str = "\n".join(f"- {p}" for p in key_points)
    prompt = f"""Draft a formal business email.
RECIPIENT: {recipient_name}
PURPOSE: {purpose}
KEY POINTS:
{points_str}
SIGNATURE: {signature}

Reply with JSON in this exact structure:
{{"subject": "...", "body": "..."}}
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL, contents=prompt)
    clean_text = response.text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(clean_text)
    except Exception:
        return {"subject": purpose, "body": response.text.strip()}


# =====================================================================
# 11. CREATE CLIENT EMAILS
# =====================================================================
def create_client_email(client_name: str, topic: str, deliverable_details: str, next_steps: str) -> Dict[str, str]:
    """Drafts client communications (proposals, progress updates, milestone deliveries)."""
    prompt = f"""Draft an executive-level client email.
CLIENT: {client_name}
TOPIC: {topic}
DELIVERABLES / UPDATES: {deliverable_details}
NEXT STEPS: {next_steps}

Reply with JSON:
{{"subject": "...", "body": "..."}}
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL, contents=prompt)
    clean_text = response.text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(clean_text)
    except Exception:
        return {"subject": f"Project Update: {topic}", "body": response.text.strip()}


# =====================================================================
# 12. CREATE COLLEGE EMAILS
# =====================================================================
def create_college_email(professor_name: str, course_code: str, topic: str, request_type: str = "extension") -> Dict[str, str]:
    """Drafts respectful, formal academic emails to professors and university administration."""
    prompt = f"""Draft a polite and respectful university email to a professor.
PROFESSOR: {professor_name}
COURSE: {course_code}
TOPIC: {topic}
REQUEST TYPE: {request_type}

Reply with JSON:
{{"subject": "...", "body": "..."}}
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL, contents=prompt)
    clean_text = response.text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(clean_text)
    except Exception:
        return {"subject": f"[{course_code}] {topic}", "body": response.text.strip()}


# =====================================================================
# 13. EXTRACT DEADLINES FROM EMAILS
# =====================================================================
def extract_deadlines_from_emails(messages: Optional[List[Dict[str, Any]]] = None, max_results: int = 15) -> List[Dict[str, Any]]:
    """Scans emails to extract all mentioned dates, deadlines, and submission milestones."""
    if messages is None:
        try:
            messages = gmail_ops.list_messages("in:inbox", max_results)
        except Exception:
            messages = []

    if not messages:
        return []

    combined = "\n\n".join(
        f"ID: {m.get('id')}\nSubject: {m.get('subject')}\nSnippet: {m.get('snippet')}"
        for m in messages
    )

    prompt = f"""Extract all specific deadlines, due dates, event dates, and meeting schedules mentioned in these emails.
EMAILS:
{combined}

Return valid JSON array of objects:
[
  {{"email_id": "...", "subject": "...", "deadline": "YYYY-MM-DD or description", "task": "..."}}
]
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL, contents=prompt)
    clean = response.text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(clean)
    except Exception:
        return []


# =====================================================================
# 14. EXTRACT ATTACHMENTS
# =====================================================================
def extract_attachments(message_id: str, output_dir: Optional[str] = None) -> Dict[str, Any]:
    """Downloads all attachments for an email message."""
    return gmail_ops.extract_attachments(message_id, save_dir=output_dir)


# =====================================================================
# 15. FIND CLIENT CONVERSATIONS
# =====================================================================
def find_client_conversations(client_name_or_domain: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """Finds all email threads associated with a client name or company domain."""
    query = f"from:{client_name_or_domain} OR to:{client_name_or_domain} OR {client_name_or_domain}"
    return search_emails(query, max_results)


# =====================================================================
# 16. FIND INVOICE & PAYMENT EMAILS
# =====================================================================
def find_invoice_payment_emails(max_results: int = 10) -> List[Dict[str, Any]]:
    """Retrieves all invoice, receipt, billing, and payment emails."""
    query = "subject:invoice OR subject:receipt OR subject:payment OR subject:bill OR 'payment receipt'"
    return search_emails(query, max_results)


# =====================================================================
# 17. FIND INTERNSHIP & JOB EMAILS
# =====================================================================
def find_job_internship_emails(max_results: int = 10) -> List[Dict[str, Any]]:
    """Retrieves all recruitment, internship, interview, and offer letters."""
    query = "internship OR 'job application' OR interview OR recruiter OR 'offer letter' OR shortlisted"
    return search_emails(query, max_results)


# =====================================================================
# 18. PREPARE FOLLOW-UP EMAILS
# =====================================================================
def prepare_followup_email(original_subject_or_id: str, context: str = "", days_since: int = 3) -> Dict[str, str]:
    """Prepares a polite, gentle follow-up email after no reply."""
    prompt = f"""Draft a gentle, professional follow-up email.
SUBJECT / CONTEXT: {original_subject_or_id}
ADDITIONAL NOTES: {context}
DAYS ELAPSED WITHOUT REPLY: {days_since}

Reply with JSON:
{{"subject": "...", "body": "..."}}
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL, contents=prompt)
    clean = response.text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(clean)
    except Exception:
        return {"subject": f"Following up: {original_subject_or_id}", "body": response.text.strip()}


# =====================================================================
# 19. EMAIL TEMPLATES
# =====================================================================
EMAIL_TEMPLATES = {
    "project_update": {
        "subject": "Project Progress Update: {project_name}",
        "body": "Hi {recipient_name},\n\nHere is a quick status update on {project_name}:\n\n- Completed: {completed_items}\n- In Progress: {in_progress_items}\n- Next Milestones: {next_milestones}\n\nPlease let me know if you have any feedback or questions.\n\nBest regards,\n{sender_name}"
    },
    "meeting_request": {
        "subject": "Meeting Request: {topic}",
        "body": "Hi {recipient_name},\n\nI would like to schedule a brief call to discuss {topic}. Are you available on {proposed_time}?\n\nLooking forward to speaking.\n\nBest regards,\n{sender_name}"
    },
    "invoice_submission": {
        "subject": "Invoice for {service_name} - {invoice_number}",
        "body": "Dear {recipient_name},\n\nPlease find attached the invoice {invoice_number} for {service_name}.\n\nTotal Due: {amount}\nDue Date: {due_date}\n\nThank you for your business.\n\nBest regards,\n{sender_name}"
    },
    "leave_application": {
        "subject": "Leave Application - {student_name} ({student_id})",
        "body": "Respected {professor_name},\n\nI am writing to request a leave of absence from {start_date} to {end_date} due to {reason}.\n\nI will make sure to catch up with all missed assignments and lecture notes promptly.\n\nThank you for your understanding.\n\nSincerely,\n{student_name}"
    }
}


def get_email_template(template_type: str, **kwargs) -> Dict[str, str]:
    """Fetches and populates pre-built templates."""
    t = EMAIL_TEMPLATES.get(template_type.lower().strip())
    if not t:
        available = list(EMAIL_TEMPLATES.keys())
        return {"error": f"Template '{template_type}' not found. Available: {available}"}

    subject = t["subject"].format(**{k: kwargs.get(k, f"[{k}]") for k in kwargs})
    body = t["body"].format(**{k: kwargs.get(k, f"[{k}]") for k in kwargs})
    return {"subject": subject, "body": body}


def list_email_templates() -> List[str]:
    """Lists available pre-built email templates."""
    return list(EMAIL_TEMPLATES.keys())


# =====================================================================
# 20. DAILY EMAIL BRIEFING
# =====================================================================
def daily_email_briefing(max_results: int = 20) -> str:
    """Generates an executive morning email summary combining unread, urgent, and pending deadlines."""
    try:
        messages = gmail_ops.list_messages("in:inbox", max_results)
    except Exception:
        messages = []

    if not messages:
        return "Daily Email Briefing: Inbox is empty or offline."

    cats = categorize_emails(messages)
    urgent = cats.get("Urgent", [])
    invoices = cats.get("Invoices", [])
    college = cats.get("College", [])
    clients = cats.get("Clients", [])

    listing = f"""Total Recent Emails: {len(messages)}
- Urgent Messages: {len(urgent)}
- Invoices / Payments: {len(invoices)}
- Client Threads: {len(clients)}
- Academic / College: {len(college)}

Recent Headlines:
""" + "\n".join(f"• From: {m['from']} | Subject: {m['subject']}" for m in messages[:8])

    prompt = f"""Generate a high-impact, 30-second morning daily email briefing for an executive/developer.
Data:
{listing}

Structure:
🌅 MORNING EMAIL BRIEFING
1. 🚨 **Immediate Attention Required** (urgent tasks/replies)
2. 💼 **Client & Work Highlights**
3. 💰 **Invoices & Finances**
4. 🎓 **College & Academics**
5. 💡 **Action Items for Today**
"""
    client = _get_client()
    response = client.models.generate_content(model=config.MODEL, contents=prompt)
    return response.text.strip()


# Direct export helpers
send = gmail_ops.send_message
mark_read = gmail_ops.mark_as_read
archive = gmail_ops.archive_message
search = search_emails
get_inbox = lambda max_results=10: read_emails("in:inbox", max_results)
get_unread = find_unread_emails
get_unread_summary = lambda max_results=10: summarize_emails("is:unread", max_results)


if __name__ == "__main__":
    print("========================================")
    print("   Orion Email Intelligence Agent")
    print("========================================")
    print("All 20 Email Features Activated.")
    print("Templates:", list_email_templates())

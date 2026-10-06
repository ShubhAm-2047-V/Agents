"""
test_email_agent.py
Quick standalone test. Requires:
1. credentials.json in this folder (Gmail OAuth client)
2. Gemini API key set in config.py

First run will open a browser to authorize Gmail access.

    python test_email_agent.py

NOTE: send() is disabled by default (config.LIVE_SEND_ENABLED = False).
This test never sends real email unless you flip that flag.
"""

from email_agent import email_agent as mail

print("=== Orion Email Agent Test ===\n")

print("1. Unread count (zero Gemini cost):")
print(" Unread:", mail.get_unread_count(), "\n")

print("2. Listing recent inbox messages (zero Gemini cost):")
messages = mail.get_inbox(max_results=5)
for m in messages:
    print(f" - {m['subject']} (from {m['from']})")
print()

print("3. Unread summary - spoken style (1 API call):")
summary = mail.get_unread_summary(max_results=10)
print(summary, "\n")

if messages:
    first_id = messages[0]["id"]

    print("4. Reading full body of first message (zero Gemini cost):")
    body = mail.read_message(first_id)
    print(" Subject:", body["subject"])
    print(" Body preview:", body["body"][:200], "...\n")

    print("5. Summarizing that email (1 API call):")
    print(mail.summarize_thread(first_id), "\n")

    print("6. Drafting a reply (1 API call) - NOT sent:")
    draft = mail.draft_reply(first_id, "thank them and say I'll respond in detail tomorrow")
    print(draft, "\n")

print("7. Drafting a brand new email from scratch (1 API call):")
new_draft = mail.draft_new_email("a short follow-up asking about project timeline")
print(new_draft)

# --- Real send - disabled by default, only works if LIVE_SEND_ENABLED = True ---
# mail.send(to="someone@example.com", subject="Test", body="This is a test.")

# Orion Email Agent

Reads, searches, drafts, and sends emails via the free Gmail API. Reading/
listing/sending are direct API calls (zero Gemini quota cost). Drafting
replies, summarizing your inbox, and composing new emails use Gemini
Flash-Lite.

## ⚠️ Safety first

- **Sending is off by default.** `config.LIVE_SEND_ENABLED = False` means
  `send()` will raise an error instead of actually sending, until you
  deliberately flip it to `True`. Test drafting first, review the output,
  then enable sending only when you trust it.
- Even with sending enabled, wire your router so it always shows you the
  drafted email and asks for confirmation before calling `send()` -
  never let a parsed voice command send email automatically.
- This runs on **your real personal Gmail account** (per your setup notes)
  - be extra careful with anything that reads/modifies your inbox.

## One-time Gmail API setup (free, ~10 minutes)

1. Go to https://console.cloud.google.com/ and create a new project (or
   use an existing one) - it's free, no billing required for this.

2. In the search bar, search for **"Gmail API"** and click **Enable**.

3. Go to **APIs & Services → OAuth consent screen**:
   - User type: **External**
   - Fill in app name (e.g. "Orion"), your email as support/developer contact
   - Under "Test users", add your own Gmail address
   - Save through the remaining steps (scopes/summary) with defaults

4. Go to **APIs & Services → Credentials → Create Credentials → OAuth
   client ID**:
   - Application type: **Desktop app**
   - Name it anything (e.g. "Orion Desktop")
   - Click **Create**, then **Download JSON**

5. Rename the downloaded file to `credentials.json` and place it directly
   in this `email_agent` folder (same level as `config.py`).

6. That's it - no API key needed for Gmail itself, just this OAuth file.
   The first time you run the agent, a browser window will open asking
   you to log in and approve access. After that, your login is cached in
   `data/token.json` and you won't need to log in again.

## Setup (rest)

1. Copy this whole `email_agent` folder into `E:\Orion\` (with
   `credentials.json` already placed inside it)

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Add your free Gemini API key (separate from Gmail) - either:
   - Set an environment variable `GEMINI_API_KEY`, OR
   - Paste it directly into `config.py`

4. Test it:
   ```
   python test_email_agent.py
   ```
   First run opens a browser for Gmail login approval.

## How it fits into Orion

```python
from email_agent import email_agent as mail

# Zero Gemini-cost, direct Gmail operations
unread_count = mail.get_unread_count()
inbox = mail.get_inbox(max_results=10)
full_email = mail.read_message(message_id)

# AI-assisted (1 Gemini call each)
briefing = mail.get_unread_summary()
summary = mail.summarize_thread(message_id)
reply_draft = mail.draft_reply(message_id, "tell them I'll be 10 min late")
new_draft = mail.draft_new_email("follow up with the recruiter about next steps")

# Sending - gated behind config.LIVE_SEND_ENABLED, always confirm with user first
mail.send(to="someone@example.com", subject="Re: Meeting", body=reply_draft)
```

## Files

| File | Purpose |
|---|---|
| `gmail_auth.py` | OAuth login flow, token caching |
| `gmail_ops.py` | Direct Gmail API calls - list/read/send/mark/archive |
| `email_agent.py` | AI layer - summarize/draft using Gemini |
| `config.py` | API key, scopes, paths, send safety gate |
| `test_email_agent.py` | Test script (send disabled by default) |

## Functions reference

**Zero Gemini-cost (direct Gmail API):**
- `search(query, max_results=10)` - Gmail search syntax, e.g. `"from:boss@company.com"`
- `get_inbox(max_results=10)`, `get_unread(max_results=10)`, `get_unread_count()`
- `read_message(message_id)` - full subject/from/date/body
- `send(to, subject, body, cc=None)` - requires `LIVE_SEND_ENABLED = True`
- `mark_read(message_id)`, `archive(message_id)`

**AI-assisted (1 Gemini Flash-Lite call each):**
- `get_unread_summary(max_results=10)` - spoken-style inbox briefing
- `summarize_thread(message_id)` - 2-3 sentence summary of one email
- `draft_reply(message_id, instruction)` - drafts a reply, doesn't send
- `draft_new_email(instruction)` - drafts subject+body from scratch, doesn't send

## Quota notes

- Gmail API has its own free quota (1 billion quota units/day) - completely
  separate from Gemini's quota, and far beyond what personal use needs.
- Only the four AI-assisted functions above touch Gemini, one call each,
  batched (e.g. `get_unread_summary` summarizes all fetched emails in a
  single call, not one call per email).

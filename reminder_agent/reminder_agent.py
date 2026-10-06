"""
reminder_agent.py
Main entry point for Orion's Reminder & Scheduling Agent.

Comprehensive 20-Feature Scheduling Suite:
1. Create reminders
2. Delete reminders
3. Modify reminders
4. Recurring reminders
5. Daily reminders
6. Weekly reminders
7. Monthly reminders
8. Exam reminders
9. Assignment reminders
10. Project deadline reminders
11. Client follow-up reminders
12. Payment reminders
13. Meeting reminders
14. Birthday reminders
15. Deadline detection
16. Reminder priorities
17. Snooze reminders
18. Morning briefing
19. Evening briefing
20. Condition-based reminders
"""

import os
import sys
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union

try:
    from . import config, reminder_store as store, notifier
except ImportError:
    import config, reminder_store as store, notifier

store.init_db()

try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


def _get_client():
    if not HAS_GENAI:
        raise RuntimeError("google-genai package is required for online AI reminder parsing.")
    return genai.Client(api_key=config.GEMINI_API_KEY)


# =====================================================================
# 1. CREATE REMINDERS
# =====================================================================
def create_reminder(
    message: str,
    due_at: Union[datetime, str],
    recurrence: Optional[str] = None,
    priority: int = 2,
    category: str = "general",
    condition: Optional[str] = None
) -> int:
    """Creates a structured reminder."""
    return store.add_reminder(
        message=message,
        due_at=due_at,
        recurrence=recurrence,
        category=category,
        priority=priority,
        condition=condition
    )


# Alias
add = create_reminder


# =====================================================================
# 2. DELETE REMINDERS
# =====================================================================
def delete_reminder(reminder_id: int) -> bool:
    """Deletes a reminder permanently."""
    return store.delete_reminder(reminder_id)


delete = delete_reminder
cancel = store.complete_reminder


# =====================================================================
# 3. MODIFY REMINDERS
# =====================================================================
def modify_reminder(
    reminder_id: int,
    message: Optional[str] = None,
    due_at: Optional[Any] = None,
    recurrence: Optional[str] = None,
    priority: Optional[int] = None,
    category: Optional[str] = None
) -> bool:
    """Updates time, message, recurrence, or priority of a reminder."""
    return store.modify_reminder(
        reminder_id=reminder_id,
        message=message,
        due_at=due_at,
        recurrence=recurrence,
        priority=priority,
        category=category
    )


# =====================================================================
# 4. RECURRING REMINDERS
# =====================================================================
def create_recurring_reminder(message: str, due_at: Union[datetime, str], recurrence: str = "daily") -> int:
    """Creates recurring reminders: daily, weekly, monthly, weekdays, yearly."""
    return store.add_reminder(message=message, due_at=due_at, recurrence=recurrence, category="recurring")


# =====================================================================
# 5. DAILY REMINDERS
# =====================================================================
def daily_reminder(message: str, time_str: str = "09:00") -> int:
    """Schedules a daily recurring reminder at HH:MM."""
    hour, minute = map(int, time_str.split(":"))
    now = datetime.now()
    target_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target_dt <= now:
        target_dt += timedelta(days=1)
    return store.add_reminder(message=message, due_at=target_dt, recurrence="daily", category="daily_routine")


# =====================================================================
# 6. WEEKLY REMINDERS
# =====================================================================
def weekly_reminder(message: str, day_of_week: str = "Monday", time_str: str = "10:00") -> int:
    """Schedules a weekly reminder on a specific weekday."""
    days_map = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6}
    target_day = days_map.get(day_of_week.lower(), 0)
    hour, minute = map(int, time_str.split(":"))
    now = datetime.now()
    days_ahead = (target_day - now.weekday() + 7) % 7
    target_dt = (now + timedelta(days=days_ahead)).replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target_dt <= now:
        target_dt += timedelta(days=7)
    return store.add_reminder(message=message, due_at=target_dt, recurrence="weekly", category="weekly_sync")


# =====================================================================
# 7. MONTHLY REMINDERS
# =====================================================================
def monthly_reminder(message: str, day_of_month: int = 1, time_str: str = "10:00") -> int:
    """Schedules a monthly reminder on day N."""
    hour, minute = map(int, time_str.split(":"))
    now = datetime.now()
    try:
        target_dt = now.replace(day=day_of_month, hour=hour, minute=minute, second=0, microsecond=0)
        if target_dt <= now:
            target_dt = (target_dt + timedelta(days=32)).replace(day=day_of_month)
    except ValueError:
        target_dt = now + timedelta(days=30)
    return store.add_reminder(message=message, due_at=target_dt, recurrence="monthly", category="monthly_routine")


# =====================================================================
# 8. EXAM REMINDERS
# =====================================================================
def exam_reminder(exam_subject: str, exam_date: Union[datetime, str], prep_alerts: bool = True) -> List[int]:
    """Creates exam alerts including revision milestones 7 days, 3 days, and 1 day prior."""
    if isinstance(exam_date, str):
        exam_dt = datetime.fromisoformat(exam_date)
    else:
        exam_dt = exam_date

    ids = []
    # Main exam reminder
    main_id = store.add_reminder(f"📝 EXAM TODAY: {exam_subject}", exam_dt, category="exam", priority=4)
    ids.append(main_id)

    if prep_alerts:
        for days in [7, 3, 1]:
            alert_dt = exam_dt - timedelta(days=days)
            if alert_dt > datetime.now():
                aid = store.add_reminder(f"📚 {days}-Day Revision Warning for {exam_subject}", alert_dt, category="exam", priority=3)
                ids.append(aid)

    return ids


# =====================================================================
# 9. ASSIGNMENT REMINDERS
# =====================================================================
def assignment_reminder(assignment_title: str, due_date: Union[datetime, str], course: str = "") -> int:
    """Creates academic assignment due date alerts."""
    prefix = f"[{course}] " if course else ""
    return store.add_reminder(f"🎓 Assignment Due: {prefix}{assignment_title}", due_date, category="assignment", priority=3)


# =====================================================================
# 10. PROJECT DEADLINE REMINDERS
# =====================================================================
def project_deadline_reminder(project_name: str, milestone: str, due_date: Union[datetime, str]) -> int:
    """Creates software project milestone and sprint deadline alerts."""
    return store.add_reminder(f"🚀 Project Deadline: '{project_name}' - {milestone}", due_date, category="project_deadline", priority=4)


# =====================================================================
# 11. CLIENT FOLLOW-UP REMINDERS
# =====================================================================
def client_followup_reminder(client_name: str, topic: str, followup_date: Union[datetime, str]) -> int:
    """Creates client follow-up and proposal review reminders."""
    return store.add_reminder(f"💼 Follow up with {client_name} regarding {topic}", followup_date, category="client_followup", priority=3)


# =====================================================================
# 12. PAYMENT REMINDERS
# =====================================================================
def payment_reminder(bill_name: str, amount: str, due_date: Union[datetime, str]) -> int:
    """Creates bill, subscription, and invoice payment reminders."""
    return store.add_reminder(f"💳 Payment Due: {bill_name} ({amount})", due_date, category="payment", priority=4)


# =====================================================================
# 13. MEETING REMINDERS
# =====================================================================
def meeting_reminder(meeting_title: str, meeting_time: Union[datetime, str], link_or_location: str = "") -> int:
    """Creates calendar meeting and zoom call alerts."""
    loc_str = f" @ {link_or_location}" if link_or_location else ""
    return store.add_reminder(f"📅 Meeting: {meeting_title}{loc_str}", meeting_time, category="meeting", priority=3)


# =====================================================================
# 14. BIRTHDAY REMINDERS
# =====================================================================
def birthday_reminder(person_name: str, birth_date: Union[datetime, str]) -> int:
    """Creates yearly recurring birthday celebrations."""
    return store.add_reminder(f"🎂 Birthday: Wish {person_name} a happy birthday!", birth_date, recurrence="yearly", category="birthday", priority=3)


# =====================================================================
# 15. DEADLINE DETECTION (NLP)
# =====================================================================
def detect_deadlines_from_text(natural_text: str) -> Dict[str, Any]:
    """Parses date, time, task, and priority from natural language instructions."""
    prompt = f"""You are a scheduling parser. Extract reminder details from this sentence.
Reference Current Datetime: {datetime.now().isoformat()}

USER TEXT: "{natural_text}"

Return ONLY valid JSON:
{{
  "message": "...",
  "due_at": "YYYY-MM-DDTHH:MM:SS",
  "recurrence": null,
  "category": "general|exam|assignment|client|payment|meeting|birthday",
  "priority": 1-4
}}
"""
    try:
        client = _get_client()
        response = client.models.generate_content(model=config.MODEL, contents=prompt)
        clean = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(clean)
    except Exception:
        # Fallback 1-hour reminder
        fallback_dt = datetime.now() + timedelta(hours=1)
        return {
            "message": natural_text,
            "due_at": fallback_dt.isoformat(),
            "recurrence": None,
            "category": "general",
            "priority": 2
        }


def add_from_text(natural_text: str) -> int:
    """Parses natural language and inserts the reminder."""
    parsed = detect_deadlines_from_text(natural_text)
    return store.add_reminder(
        message=parsed.get("message", natural_text),
        due_at=parsed.get("due_at", datetime.now() + timedelta(hours=1)),
        recurrence=parsed.get("recurrence"),
        category=parsed.get("category", "general"),
        priority=parsed.get("priority", 2)
    )


# =====================================================================
# 16. REMINDER PRIORITIES
# =====================================================================
def set_priority(reminder_id: int, priority_level: int) -> bool:
    """Sets priority level (1=Low, 2=Medium, 3=High, 4=Urgent)."""
    return store.modify_reminder(reminder_id, priority=priority_level)


# =====================================================================
# 17. SNOOZE REMINDERS
# =====================================================================
def snooze(reminder_id: int, minutes: int = 15) -> Optional[str]:
    """Snoozes a reminder by N minutes."""
    return store.snooze_reminder(reminder_id, minutes=minutes)


# =====================================================================
# 18. MORNING BRIEFING
# =====================================================================
def morning_briefing() -> str:
    """Returns an executive agenda of all tasks and reminders scheduled for today."""
    all_reminders = store.get_all_reminders(include_completed=False)
    today = datetime.now().date()
    today_items = []

    for r in all_reminders:
        try:
            dt = datetime.fromisoformat(r["due_at"])
            if dt.date() == today:
                today_items.append(r)
        except Exception:
            pass

    if not today_items:
        return "Good Morning! You have no scheduled tasks or reminders due today."

    lines = [f"- [{r.get('category', 'task').upper()}] {r['message']} (at {datetime.fromisoformat(r['due_at']).strftime('%I:%M %p')})" for r in today_items]
    return f"--- MORNING SCHEDULE BRIEFING ({len(today_items)} Items Today) ---\n" + "\n".join(lines)


# =====================================================================
# 19. EVENING BRIEFING
# =====================================================================
def evening_briefing() -> str:
    """Returns end-of-day summary of pending tasks and a lookahead for tomorrow."""
    all_reminders = store.get_all_reminders(include_completed=False)
    tomorrow = datetime.now().date() + timedelta(days=1)
    tomorrow_items = []

    for r in all_reminders:
        try:
            dt = datetime.fromisoformat(r["due_at"])
            if dt.date() == tomorrow:
                tomorrow_items.append(r)
        except Exception:
            pass

    lines = [f"- {r['message']} ({datetime.fromisoformat(r['due_at']).strftime('%I:%M %p')})" for r in tomorrow_items]
    tomorrow_text = "\n".join(lines) if lines else "No scheduled tasks for tomorrow."
    return f"--- EVENING RECAP & TOMORROW'S PREVIEW ---\n{tomorrow_text}"


# =====================================================================
# 20. CONDITION-BASED REMINDERS
# =====================================================================
def create_condition_reminder(message: str, condition: str = "when_idle") -> int:
    """Creates reminders triggered on condition (when_idle, battery_low, on_app_open)."""
    return store.add_reminder(
        message=message,
        due_at=datetime.now() + timedelta(days=365),
        category="condition",
        condition=condition
    )


# Execution & background helpers
def list_active():
    return store.get_all_reminders(include_completed=False)


def list_all():
    return store.get_all_reminders(include_completed=True)


def check_and_fire_due():
    due = store.get_due_reminders()
    for r in due:
        notifier.notify(r["message"])
        store.mark_fired(r["id"])
    return due


def run_checker_loop(interval=None, max_iterations=None):
    interval = interval or config.CHECK_INTERVAL_SECONDS
    count = 0
    while True:
        check_and_fire_due()
        count += 1
        if max_iterations and count >= max_iterations:
            break
        time.sleep(interval)


def start_background_checker(interval=None):
    t = threading.Thread(target=run_checker_loop, kwargs={"interval": interval}, daemon=True)
    t.start()
    return t


if __name__ == "__main__":
    print("========================================")
    print("    Orion Reminder & Scheduler Agent")
    print("========================================")
    print("All 20 Scheduling Features Activated.")
    print("Active Reminders:", len(list_active()))
    print("\n" + morning_briefing())

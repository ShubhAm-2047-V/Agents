"""
notifier.py
Handles actually delivering a reminder to the user when it's due.
Zero API cost - just local notification methods.
"""

try:
    from . import config
except ImportError:
    import config


def notify(message):
    """Dispatches to the configured notification method."""
    if config.NOTIFY_METHOD == "windows_toast":
        _notify_windows_toast(message)
    else:
        _notify_console(message)


def _notify_console(message):
    print(f"\n🔔 REMINDER: {message}\n")


def _notify_windows_toast(message):
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast("Orion Reminder", message, duration=10, threaded=True)
    except ImportError:
        print("[notifier] win10toast not installed - falling back to console.")
        _notify_console(message)

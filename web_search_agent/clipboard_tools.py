"""
clipboard_tools.py
Handles Windows clipboard AI operations (summarize clipboard, fix grammar, translate)
and QR code generation (terminal ASCII display + image file export).
"""

import os
import sys
import time
import pyperclip
import config

try:
    import qrcode
except ImportError:
    qrcode = None

try:
    from google import genai
except ImportError:
    genai = None


def _get_client():
    if genai and config.GEMINI_API_KEY and config.GEMINI_API_KEY != "PASTE_YOUR_GEMINI_API_KEY_HERE":
        return genai.Client(api_key=config.GEMINI_API_KEY)
    return None


def get_clipboard() -> str:
    """Gets current text content from system clipboard."""
    try:
        return pyperclip.paste().strip()
    except Exception:
        return ""


def set_clipboard(text: str) -> bool:
    """Copies text to the system clipboard."""
    try:
        pyperclip.copy(text)
        return True
    except Exception:
        return False


def process_clipboard_ai(action: str = "summarize", extra_prompt: str = None) -> tuple[bool, str, str]:
    """
    Reads clipboard text, processes it with Gemini AI according to action,
    updates clipboard with the output, and returns results.
    Returns: (success: bool, processed_text: str, message: str)
    """
    text = get_clipboard()
    if not text:
        return False, "", "⚠️ Your clipboard is empty or does not contain text."

    client = _get_client()
    if not client:
        return False, text[:300], "⚠️ Gemini API Key required for Clipboard AI actions."

    action_lower = action.lower()
    if "fix" in action_lower or "grammar" in action_lower or "proofread" in action_lower:
        instructions = "Fix all grammar, punctuation, spelling, and tone issues in this text. Make it sound professional and crisp while preserving the original meaning. Output ONLY the corrected text."
    elif "translate" in action_lower:
        target_lang = extra_prompt or "English"
        instructions = f"Translate the following text into {target_lang}. Preserve tone and formatting. Output ONLY the translation."
    elif "bullet" in action_lower or "points" in action_lower:
        instructions = "Transform the following text into high-impact, punchy bullet points. Output ONLY the bullet list."
    else:  # default: summarize
        instructions = "Provide a concise executive summary of this clipboard text in 2-3 crisp sentences followed by 3 key takeaways. Do NOT use markdown tables."

    prompt = f"""{instructions}

CLIPBOARD CONTENT:
{text[:10000]}
"""

    try:
        response = client.models.generate_content(model=config.MODEL, contents=prompt)
        output_text = response.text.strip()
        set_clipboard(output_text)
        return True, output_text, "✅ Copied result back to your clipboard ready to paste (Ctrl+V)!"
    except Exception as e:
        return False, "", f"Error processing clipboard: {e}"


def generate_qr_code(data: str) -> tuple[bool, str, str]:
    """
    Generates a QR code image saved to exports/ and returns an ASCII string representation
    for instant terminal scanning.
    Returns: (success: bool, file_path: str, ascii_qr: str)
    """
    if not qrcode:
        return False, "", "⚠️ 'qrcode' library is required."

    os.makedirs(config.EXPORT_DIR, exist_ok=True)
    filename = f"qrcode_{int(time.time())}.png"
    file_path = os.path.join(config.EXPORT_DIR, filename)

    try:
        # 1. Generate PNG Image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(file_path)

        # 2. Generate ASCII QR Code for Terminal
        import io
        f = io.StringIO()
        qr.print_ascii(out=f, invert=True)
        ascii_qr = f.getvalue()

        if getattr(config, "AUTO_OPEN_EXPORTS", True):
            try:
                os.startfile(file_path)
            except Exception:
                pass

        return True, file_path, ascii_qr
    except Exception as e:
        return False, "", f"Error generating QR code: {e}"

# Orion Brightness & Volume Control Agent

Zero-cost, instant hardware control for Windows screen brightness, master audio volume, per-app sound levels, media playback keys, and atmosphere presets.

## 🚀 Key Features

- **Screen Brightness**: Get, set, increase, decrease, dim, and max brightness across connected monitors.
- **Master Audio Volume**: Accurate scalar volume (0-100%), relative up/down step controls, mute/unmute, and toggle mute.
- **Per-App Audio Control**: Set volume or mute individual running apps (e.g. `chrome`, `spotify`, `discord`, `vlc`, games).
- **Media Playback Keys**: Hardware media control simulation (Play/Pause, Next Track, Previous Track, Stop).
- **Atmosphere Presets**: Instant multi-setting profiles (`movie`, `night`, `gaming`, `study`, `focus`, `work`, `daylight`, `sleep`, `reset`).
- **100% Offline by Default**: Intelligent regex & semantic rule parser handles compound and natural language commands with 0 API calls and zero latency.
- **Optional Gemini AI Fallback**: Advanced natural language reasoning when online mode is enabled.
- **Interactive Visual CLI**: Real-time terminal telemetry dashboard with live progress bars and active audio session monitor.

---

## 📦 Setup & Dependencies

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(Packages: `pycaw`, `screen-brightness-control`, `comtypes`, `psutil`, `colorama`, `google-genai`)*

2. Optional Gemini API Key:
   - Set environment variable `GEMINI_API_KEY`, or
   - Paste into `config.py`
   *(By default, runs 100% offline with zero setup required)*

3. Test the agent:
   ```bash
   python test_volume_brightness.py
   ```

4. Run the interactive dashboard:
   ```bash
   run.bat
   ```

---

## 💻 Usage in Python Router / Orion Core

```python
from volume_brightness_agent import volume_brightness_agent as media
1. **🔊 Master Volume & Display Brightness Control**
   - Direct, smooth hardware volume and screen brightness adjustments (0-100%).
   - Multi-monitor brightness support with WMI/VCP fallbacks.

2. **🎧 Audio Output Device Switcher**
   - Switch Windows default audio playback between Laptop Speakers, Headphones, Bluetooth Earbuds, or HDMI.
   - Example: `switch to headphones`, `switch to speakers`, `devices`.

3. **🎙️ Global Microphone Control & Privacy Indicator**
   - Dedicated mic recording level and global mute toggle.
   - Example: `mute mic`, `unmute mic`, `mic volume 80%`.

4. **🎵 "Now Playing" Song & Artist Detector**
   - Uses Windows GSMTC (Global System Media Transport Controls) to detect track, artist, album, and app playing on Spotify, YouTube, Chrome, or media players.
   - Example: `what's playing`, `song`, `play`, `pause`, `next track`.

5. **⏳ Sleep Timer & Smooth Volume Fade-Out**
   - Sets a timer that gradually fades volume down to 0% before muting or turning off the screen.
   - Example: `sleep timer 30 mins`, `fade volume in 20 minutes`, `cancel sleep timer`.

6. **⏰ Circadian Auto-Brightness (Day/Night Sync)**
   - Automatically calculates ideal screen brightness based on the local time of day.
   - Example: `circadian on`, `circadian off`, `sync brightness`, `auto brightness`.

7. **🎛️ Per-App Audio Mixer**
   - Individual app sliders for Spotify, Chrome, Discord, VLC, Games, etc.
   - Example: `mute spotify`, `unmute chrome`, `set spotify volume to 40%`, `discord volume 30`.

8. **🎬 Atmosphere Presets System & In-CMD Customizer**
   - Built-in presets: `movie`, `night`, `gaming`, `study`, `focus`, `sleep`, `work`, `daylight`, `presentation`.
   - In-terminal wizard: Type `customize` or `c` to edit brightness, volume, and mute settings permanently.

---

## 💻 Natural Language Command Examples

| Category | Example Commands |
|---|---|
| **Audio Device Switcher** | `switch to headphones`, `switch to speakers`, `switch to bluetooth`, `devices` |
| **Microphone Control** | `mute mic`, `unmute mic`, `toggle mic`, `mic volume 80%`, `mic` |
| **Now Playing Music** | `what's playing`, `now playing`, `song`, `play`, `pause`, `next`, `prev` |
| **Sleep Timer & Fade** | `sleep timer 30 mins`, `fade volume in 20 minutes`, `cancel sleep timer` |
| **Circadian Brightness** | `circadian on`, `circadian off`, `auto brightness`, `sync brightness` |
| **Volume Control** | `vol 60`, `set volume to 75%`, `turn it up`, `volume down by 15`, `mute`, `unmute` |
| **Brightness Control** | `brightness 80%`, `screen 60`, `dim screen`, `make screen brighter`, `max brightness` |
| **Per-App Mixer** | `mute spotify`, `unmute chrome`, `set spotify volume to 40%`, `discord volume 30` |
| **Atmosphere Presets** | `movie mode`, `night mode`, `gaming mode`, `study mode`, `focus mode`, `sleep mode` |
| **Compound Commands** | `set volume to 30 and brightness to 80`, `dim screen and mute` |
| **In-CMD Tools** | `customize` (edit presets), `dashboard` / `dash`, `mixer`, `presets`, `summary`, `cls` |

---

## 🏃 Quick Start

Run standalone from Command Prompt:
```cmd
E:\Agent's\volume_brightness_agent\run.bat
```
Or launch from the main menu:
```cmd
E:\Agent's\run_menu.bat
```
Select **`[9] Brightness & Volume Agent`**.

---

## 📁 Files

| File | Description |
|---|---|
| `volume_brightness_agent.py` | Main agent entry point, direct API, NLP parser, CLI dashboard |
| `media_ops.py` | Core low-level Pycaw, ScreenBrightnessControl, Win32 media keys |
| `config.py` | Settings, step sizes, aliases, and preset configurations |
| `test_volume_brightness.py` | Automated test suite |
| `run.bat` | Windows batch launcher |
| `requirements.txt` | Python package dependencies |

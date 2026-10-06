"""
test_volume_brightness.py
Test suite for Orion's Brightness & Volume Control Agent.
"""

import sys
import os

# Enable UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import volume_brightness_agent as agent
    import media_ops
    import config
except ImportError:
    from . import volume_brightness_agent as agent
    from . import media_ops
    from . import config


def run_tests():
    print("==================================================")
    print("Testing Orion Brightness & Volume Control Agent")
    print("==================================================")

    # 1. Test Telemetry / Reading
    print("\n[1] Testing Hardware Status Readouts:")
    vol = agent.get_volume()
    print(f"   ✓ Volume status: {vol}")
    assert isinstance(vol, dict) and "level" in vol

    bri = agent.get_brightness()
    print(f"   ✓ Brightness status: {bri}")
    assert isinstance(bri, dict) and "level" in bri

    summary = agent.get_spoken_summary()
    print(f"   ✓ Spoken summary: '{summary}'")
    assert len(summary) > 5

    # 2. Test Offline NLP Parser
    print("\n[2] Testing Offline NLP Command Parser:")
    test_phrases = [
        ("set volume to 75%", "set_volume", 75),
        ("vol 50", "set_volume", 50),
        ("turn it down", "volume_down", 10),
        ("volume up by 15", "volume_up", 15),
        ("mute audio", "mute", None),
        ("unmute", "unmute", None),
        ("set brightness to 80%", "set_brightness", 80),
        ("screen 65", "set_brightness", 65),
        ("dim screen", "brightness_down", 10),
        ("make screen brighter by 20", "brightness_up", 20),
        ("max brightness", "max_brightness", None),
        ("min brightness", "min_brightness", None),
        ("movie mode", "apply_preset", "movie"),
        ("gaming preset", "apply_preset", "gaming"),
        ("night mode", "apply_preset", "night"),
        ("study mode", "apply_preset", "study"),
        ("mute spotify", "mute_app", "spotify"),
        ("set spotify volume to 40%", "set_app_volume", 40),
        ("set volume to 30 and brightness to 80", "compound", 2),
        ("dim screen and mute", "compound", 2),
        ("play", "media_play_pause", None),
        ("next track", "media_next", None)
    ]

    for phrase, expected_action, expected_val in test_phrases:
        parsed = agent.parse_command(phrase)
        actions = parsed.get("actions", [])
        assert len(actions) > 0, f"Failed to parse: '{phrase}'"
        
        if expected_action == "compound":
            assert len(actions) >= expected_val, f"Expected {expected_val} actions for '{phrase}', got {len(actions)}"
            print(f"   ✓ Compound '{phrase}' -> {len(actions)} actions parsed")
        else:
            first_act = actions[0].get("action")
            assert first_act == expected_action, f"Expected {expected_action} for '{phrase}', got {first_act}"
            print(f"   ✓ '{phrase}' -> action '{first_act}'")

    # 3. Test Presets Dictionary
    print("\n[3] Testing Preset Registry:")
    presets = agent.list_presets()
    assert "movie" in presets
    assert "night" in presets
    assert "gaming" in presets
    assert "study" in presets
    print(f"   ✓ {len(presets)} atmosphere presets available: {', '.join(presets.keys())}")

    # 4. Test Audio Sessions
    print("\n[4] Testing Audio Session Enumeration:")
    apps = agent.list_apps()
    print(f"   ✓ Found {len(apps)} active audio session(s)")
    for app in apps:
        print(f"     • {app.get('name')}: {app.get('level')}% (Muted: {app.get('is_muted')})")

    # 5. Test 5 New Advanced Features
    print("\n[5] Testing 5 Advanced Media Capabilities:")
    # 5.1 Device Switcher
    devices = agent.list_devices()
    print(f"   ✓ Audio devices detected: {len(devices)}")
    assert isinstance(devices, list)

    # 5.2 Microphone
    mic_st = agent.get_mic()
    print(f"   ✓ Microphone status: {mic_st}")
    assert isinstance(mic_st, dict) and "level" in mic_st

    # 5.3 Now Playing
    now_p = agent.now_playing()
    print(f"   ✓ Now playing readout: {now_p.get('display')}")
    assert isinstance(now_p, dict) and "title" in now_p

    # 5.4 Sleep Timer
    st_res = agent.sleep_timer(60, action="mute")
    print(f"   ✓ Start sleep timer: {st_res}")
    st_status = media_ops.get_sleep_timer_status()
    assert st_status.get("active") is True
    cancel_res = agent.cancel_sleep_timer()
    print(f"   ✓ Cancel sleep timer: {cancel_res}")

    # 5.5 Circadian Sync
    circ_bri = media_ops.get_circadian_brightness()
    print(f"   ✓ Circadian target brightness for current hour: {circ_bri}%")
    assert 0 <= circ_bri <= 100

    # 6. Test NLP Parser for 5 New Features
    print("\n[6] Testing NLP Parser on 5 New Feature Queries:")
    new_phrases = [
        ("switch to headphones", "switch_device"),
        ("switch to speakers", "switch_device"),
        ("devices", "list_devices"),
        ("mute mic", "mute_mic"),
        ("unmute mic", "unmute_mic"),
        ("mic volume 80%", "set_mic_volume"),
        ("what's playing", "now_playing"),
        ("song", "now_playing"),
        ("sleep timer 30 mins", "sleep_timer"),
        ("cancel sleep timer", "cancel_sleep_timer"),
        ("circadian on", "toggle_circadian"),
        ("auto brightness", "circadian_sync")
    ]
    for ph, expected_act in new_phrases:
        parsed = agent.parse_command(ph)
        acts = parsed.get("actions", [])
        assert len(acts) > 0, f"Failed parsing new phrase: '{ph}'"
        assert acts[0].get("action") == expected_act, f"Expected {expected_act} for '{ph}', got {acts[0].get('action')}"
        print(f"   ✓ '{ph}' -> action '{expected_act}'")

    # 7. Non-disruptive Hardware Step Test (Read -> Set -> Restore)
    print("\n[7] Testing Non-disruptive Set & Restore Execution:")
    orig_vol = vol.get("level", 50)
    orig_bri = bri.get("level", 50)

    # Temporary minor adjustment
    test_vol = max(10, min(90, orig_vol + 5 if orig_vol < 80 else orig_vol - 5))
    res_vol = agent.set_volume(test_vol)
    print(f"   ✓ {res_vol}")
    
    # Restore original volume
    agent.set_volume(orig_vol)
    print(f"   ✓ Restored volume to {orig_vol}%")

    test_bri = max(10, min(90, orig_bri + 5 if orig_bri < 80 else orig_bri - 5))
    res_bri = agent.set_brightness(test_bri)
    print(f"   ✓ {res_bri}")

    # Restore original brightness
    agent.set_brightness(orig_bri)
    print(f"   ✓ Restored brightness to {orig_bri}%")

    print("\n==================================================")
    print(" ALL TESTS PASSED SUCCESSFULLY! (100% Zero Error)")
    print("==================================================")


if __name__ == "__main__":
    run_tests()


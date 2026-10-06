"""
ui.py
Orion Central Brain - Ultra-Compact Floating Command Center & HUD.
Featuring a sleek, scrollable Command Palette drawer with mouse wheel scrolling,
live telemetry, and multi-agent dispatching.
"""

import os
import sys
import time
import json
import threading
from typing import Optional, List, Dict, Any

# Ensure workspace root in sys.path
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

import customtkinter as ctk
import tkinter as tk

from central_brain.brain import CentralBrain, BrainResult
from central_brain.agent_registry import REGISTRY
import central_brain.config as config

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

AGENT_THEMES = {
    "volume_brightness_agent": {"icon": "🔊", "color": "#06B6D4", "label": "Hardware"},
    "app_control_agent": {"icon": "💻", "color": "#3B82F6", "label": "App Control"},
    "system_monitor_agent": {"icon": "📊", "color": "#10B981", "label": "Telemetry"},
    "reminder_agent": {"icon": "⏰", "color": "#F59E0B", "label": "Reminder"},
    "file_manager_agent": {"icon": "📁", "color": "#8B5CF6", "label": "Files"},
    "memory_agent": {"icon": "🧠", "color": "#EC4899", "label": "Memory"},
    "code_assistant_agent": {"icon": "⚡", "color": "#6366F1", "label": "Code"},
    "email_agent": {"icon": "📧", "color": "#EF4444", "label": "Email"},
    "web_search_agent": {"icon": "🌐", "color": "#14B8A6", "label": "Web"},
}

# Categorized Command Catalog
COMMAND_GROUPS = {
    "🔊 Hardware": [
        ("🎬 Movie Preset", "movie mode"),
        ("🎮 Gaming Preset", "gaming mode"),
        ("🌙 Night Preset", "night mode"),
        ("📖 Study Preset", "study mode"),
        ("☀️ Daylight Preset", "daylight mode"),
        ("🔊 Vol 100% (Max)", "set volume to 100"),
        ("🔊 Vol 75%", "set volume to 75"),
        ("🔊 Vol 50%", "set volume to 50"),
        ("🔊 Vol 25%", "set volume to 25"),
        ("🔇 Mute Audio", "mute"),
        ("🔈 Unmute Audio", "unmute"),
        ("🔆 Max Brightness", "set brightness to 100"),
        ("🔅 Dim Screen (30%)", "dim screen"),
        ("⏯️ Play / Pause", "play pause"),
        ("⏭️ Next Track", "next track"),
        ("⏮️ Previous Track", "previous track"),
    ],
    "📊 System": [
        ("📊 System Snapshot", "system stats"),
        ("🩺 PC Health Score", "pc health"),
        ("⚡ Check CPU Usage", "cpu usage"),
        ("💾 Check RAM Usage", "how much ram is free"),
        ("🎮 Check GPU Stats", "check gpu"),
        ("💽 Check Disks", "check disks"),
        ("🔋 Battery Health", "check battery"),
        ("🌡️ Temperatures", "check temps"),
        ("🔥 Top CPU Hogs", "high cpu processes"),
        ("📈 Top RAM Hogs", "high ram processes"),
    ],
    "💻 Apps": [
        ("💻 List Running Apps", "list running apps"),
        ("🪟 Open Windows", "show open windows"),
        ("🌐 Open Chrome", "open chrome"),
        ("📝 Open Notepad", "open notepad"),
        ("💬 Open Discord", "open discord"),
        ("🎵 Open Spotify", "open spotify"),
        ("💻 Open VS Code", "open code"),
        ("🗔 Minimize All", "minimize all"),
        ("↔️ Side-by-Side", "side by side chrome and notepad"),
    ],
    "⏰ Reminders": [
        ("🌅 Morning Briefing", "morning briefing"),
        ("🌆 Evening Briefing", "evening briefing"),
        ("📋 List Reminders", "list reminders"),
        ("⏰ Break in 10m", "remind me in 10 minutes to take a quick break"),
        ("⏰ Tomorrow 9 AM", "remind me tomorrow at 9am to check updates"),
    ],
    "📁 Files": [
        ("🧹 Clean Desktop", "clean desktop"),
        ("📥 Clean Downloads", "clean downloads"),
        ("🔍 Duplicate Files", "find duplicate files"),
        ("🐘 Storage Hogs", "storage hogs"),
        ("🕒 Recent Files", "recently modified files"),
        ("🔎 Search *.py", "search file *.py"),
        ("🔎 Search *.pdf", "search file *.pdf"),
    ],
    "🧠 Memory": [
        ("💾 List Memories", "list memories"),
        ("👤 My Preferences", "what is my preference"),
        ("🔍 Search Memory", "search memory for project"),
        ("📌 Save Fact", "remember that my primary system is Orion Brain"),
    ],
    "⚡ Code": [
        ("💡 Explain Code", "explain this code"),
        ("🐍 Write REST API", "write python script to fetch a REST api"),
        ("🐛 Fix Code Bugs", "fix bug in this code"),
        ("⚡ Optimize Code", "optimize this slow code"),
        ("🧪 Unit Tests", "generate unit tests for this code"),
    ],
    "📧 Email": [
        ("📥 Read Inbox", "read emails"),
        ("✉️ Unread Emails", "find unread emails"),
        ("⭐ Important Emails", "find important emails"),
        ("📰 Daily Briefing", "daily email briefing"),
    ],
    "🌐 Web": [
        ("🌐 Open My Website (Shubdeep Labs)", "open my website"),
        ("🤖 AI Latest News", "latest news on artificial intelligence"),
        ("🌦️ Weather Forecast", "what is the weather today"),
        ("📈 Stock (NVDA)", "stock price of NVDA"),
        ("📈 Stock (AAPL)", "stock price of AAPL"),
        ("🔍 Fact Check", "fact check quantum computing advances"),
    ]
}


class OrionBrainHUD(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.brain = CentralBrain()
        self.cmd_history: List[str] = []
        self.history_index: int = -1
        self.is_pinned: bool = True
        self.is_menu_open: bool = False
        self.is_result_open: bool = False

        # Ultra-Compact Base Dimensions
        self.hud_w = 410
        self.base_h = 108
        self.menu_h = 290
        self.result_h = 260

        self.title("Orion Brain")
        self.geometry(f"{self.hud_w}x{self.base_h}")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.96)
        self.configure(fg_color="#0B0F19")

        # Drag Window Handlers
        self._offset_x = 0
        self._offset_y = 0

        self._init_ui()
        self._start_telemetry_loop()

    def _init_ui(self):
        # ---------------- 1. Micro Top Bar ----------------
        self.top_bar = ctk.CTkFrame(self, fg_color="#111827", corner_radius=6, height=24)
        self.top_bar.pack(fill="x", padx=4, pady=(4, 2))
        self.top_bar.bind("<ButtonPress-1>", self._on_drag_start)
        self.top_bar.bind("<B1-Motion>", self._on_drag_motion)

        self.lbl_brand = ctk.CTkLabel(
            self.top_bar,
            text="🧠 ORION",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#38BDF8"
        )
        self.lbl_brand.pack(side="left", padx=(6, 4), pady=2)
        self.lbl_brand.bind("<ButtonPress-1>", self._on_drag_start)
        self.lbl_brand.bind("<B1-Motion>", self._on_drag_motion)

        self.lbl_telemetry = ctk.CTkLabel(
            self.top_bar,
            text="C:--% | R:--%",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            text_color="#10B981"
        )
        self.lbl_telemetry.pack(side="left", padx=4, pady=2)
        self.lbl_telemetry.bind("<ButtonPress-1>", self._on_drag_start)
        self.lbl_telemetry.bind("<B1-Motion>", self._on_drag_motion)

        # Close
        self.btn_close = ctk.CTkButton(
            self.top_bar,
            text="✕",
            width=18,
            height=18,
            fg_color="#EF4444",
            hover_color="#DC2626",
            font=ctk.CTkFont(size=9, weight="bold"),
            command=self.destroy
        )
        self.btn_close.pack(side="right", padx=(2, 4), pady=2)

        # Output Toggle
        self.btn_out_toggle = ctk.CTkButton(
            self.top_bar,
            text="📋 Log",
            width=36,
            height=18,
            fg_color="#1F2937",
            hover_color="#374151",
            font=ctk.CTkFont(size=9),
            command=self.toggle_result_drawer
        )
        self.btn_out_toggle.pack(side="right", padx=2, pady=2)

        # Pin
        self.btn_pin = ctk.CTkButton(
            self.top_bar,
            text="📌",
            width=24,
            height=18,
            fg_color="#0284C7",
            hover_color="#0369A1",
            font=ctk.CTkFont(size=9),
            command=self.toggle_pin
        )
        self.btn_pin.pack(side="right", padx=2, pady=2)

        # ---------------- 2. Input & Actions Button Bar ----------------
        self.input_card = ctk.CTkFrame(self, fg_color="#111827", corner_radius=6, height=36)
        self.input_card.pack(fill="x", padx=4, pady=2)

        # Scrollable Drawer Action Button
        self.btn_actions = ctk.CTkButton(
            self.input_card,
            text="⚡ Actions ▾",
            width=84,
            height=26,
            fg_color="#1F2937",
            hover_color="#374151",
            font=ctk.CTkFont(size=10, weight="bold"),
            command=self.toggle_action_menu
        )
        self.btn_actions.pack(side="left", padx=(4, 2), pady=3)

        self.cmd_entry = ctk.CTkEntry(
            self.input_card,
            placeholder_text="Enter any command or question...",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            fg_color="#070A11",
            border_color="#0284C7",
            border_width=1,
            text_color="#F8FAFC",
            height=26
        )
        self.cmd_entry.pack(side="left", fill="x", expand=True, padx=2, pady=3)
        self.cmd_entry.bind("<Return>", lambda e: self.on_execute())
        self.cmd_entry.bind("<Up>", self._on_history_up)
        self.cmd_entry.bind("<Down>", self._on_history_down)

        self.btn_send = ctk.CTkButton(
            self.input_card,
            text="RUN",
            width=42,
            height=26,
            fg_color="#0284C7",
            hover_color="#0369A1",
            font=ctk.CTkFont(size=10, weight="bold"),
            command=self.on_execute
        )
        self.btn_send.pack(side="right", padx=(2, 4), pady=3)

        # ---------------- 3. Status Bar ----------------
        self.status_bar = ctk.CTkFrame(self, fg_color="transparent", height=18)
        self.status_bar.pack(fill="x", padx=6, pady=(1, 2))

        self.lbl_agent_badge = ctk.CTkLabel(
            self.status_bar,
            text="● Central Brain Ready",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color="#38BDF8"
        )
        self.lbl_agent_badge.pack(side="left")

        self.lbl_route_type = ctk.CTkLabel(
            self.status_bar,
            text="STANDBY",
            font=ctk.CTkFont(family="Consolas", size=8),
            text_color="#64748B"
        )
        self.lbl_route_type.pack(side="right")

        # ---------------- 4. Compact Scrollable Actions Palette (Mouse-Scrollable) ----------------
        self.menu_drawer = ctk.CTkFrame(self, fg_color="#111827", corner_radius=6)
        
        self.menu_scroll = ctk.CTkScrollableFrame(
            self.menu_drawer,
            fg_color="#0B0F19",
            corner_radius=4,
            height=160
        )
        self.menu_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        # Populate Categorized Buttons with Mouse-Wheel Scroll Binding
        for category, commands in COMMAND_GROUPS.items():
            # Category Header
            lbl_cat = ctk.CTkLabel(
                self.menu_scroll,
                text=f"— {category} —",
                font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
                text_color="#38BDF8",
                anchor="w"
            )
            lbl_cat.pack(fill="x", padx=4, pady=(6, 2))

            # Command Buttons in 2-column or full width
            for label, cmd_text in commands:
                btn = ctk.CTkButton(
                    self.menu_scroll,
                    text=label,
                    height=22,
                    fg_color="#1F2937",
                    hover_color="#0284C7",
                    text_color="#E2E8F0",
                    font=ctk.CTkFont(size=9),
                    anchor="w",
                    command=lambda c=cmd_text: self._execute_from_palette(c)
                )
                btn.pack(fill="x", padx=2, pady=1)

        # Bind mouse wheel to scroll smoothly
        self._bind_mousewheel(self.menu_scroll)

        # ---------------- 5. Result Output Drawer ----------------
        self.result_drawer = ctk.CTkFrame(self, fg_color="#111827", corner_radius=6)

        self.result_tools = ctk.CTkFrame(self.result_drawer, fg_color="transparent", height=18)
        self.result_tools.pack(fill="x", padx=4, pady=(2, 1))

        self.lbl_feed_title = ctk.CTkLabel(
            self.result_tools,
            text="Execution Result",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="#94A3B8"
        )
        self.lbl_feed_title.pack(side="left")

        self.btn_copy = ctk.CTkButton(
            self.result_tools,
            text="📋 Copy",
            width=42,
            height=16,
            fg_color="#1F2937",
            hover_color="#374151",
            font=ctk.CTkFont(size=8),
            command=self.copy_output
        )
        self.btn_copy.pack(side="right", padx=2)

        self.btn_clear = ctk.CTkButton(
            self.result_tools,
            text="🗑 Clear",
            width=42,
            height=16,
            fg_color="#1F2937",
            hover_color="#374151",
            font=ctk.CTkFont(size=8),
            command=self.clear_output
        )
        self.btn_clear.pack(side="right", padx=2)

        self.output_box = ctk.CTkTextbox(
            self.result_drawer,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color="#070A11",
            text_color="#E2E8F0",
            corner_radius=4,
            wrap="word"
        )
        self.output_box.pack(fill="both", expand=True, padx=4, pady=(1, 4))

    # ---------------- Mouse Wheel Smooth Scroll ----------------
    def _bind_mousewheel(self, widget):
        def _on_mousewheel(event):
            try:
                # On Windows event.delta is typically +/- 120
                widget._parent_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            except Exception:
                pass
        widget.bind_all("<MouseWheel>", _on_mousewheel)

    # ---------------- Window Dragging ----------------
    def _on_drag_start(self, event):
        self._offset_x = event.x
        self._offset_y = event.y

    def _on_drag_motion(self, event):
        x = self.winfo_x() + (event.x - self._offset_x)
        y = self.winfo_y() + (event.y - self._offset_y)
        self.geometry(f"+{x}+{y}")

    # ---------------- Controls & Drawers ----------------
    def toggle_pin(self):
        self.is_pinned = not self.is_pinned
        self.attributes("-topmost", self.is_pinned)
        if self.is_pinned:
            self.btn_pin.configure(fg_color="#0284C7")
        else:
            self.btn_pin.configure(fg_color="#374151")

    def toggle_action_menu(self):
        self.is_menu_open = not self.is_menu_open
        if self.is_menu_open:
            # Close result drawer if open to save space
            if self.is_result_open:
                self.result_drawer.pack_forget()
                self.is_result_open = False
                self.btn_out_toggle.configure(fg_color="#1F2937")

            self.menu_drawer.pack(fill="both", expand=True, padx=4, pady=(1, 4))
            self.geometry(f"{self.hud_w}x{self.menu_h}")
            self.btn_actions.configure(text="⚡ Actions ▴", fg_color="#0284C7")
        else:
            self.menu_drawer.pack_forget()
            self.geometry(f"{self.hud_w}x{self.base_h}")
            self.btn_actions.configure(text="⚡ Actions ▾", fg_color="#1F2937")

    def toggle_result_drawer(self, force_open: Optional[bool] = None):
        if force_open is not None:
            self.is_result_open = force_open
        else:
            self.is_result_open = not self.is_result_open

        if self.is_result_open:
            # Close action menu if open
            if self.is_menu_open:
                self.menu_drawer.pack_forget()
                self.is_menu_open = False
                self.btn_actions.configure(text="⚡ Actions ▾", fg_color="#1F2937")

            self.result_drawer.pack(fill="both", expand=True, padx=4, pady=(1, 4))
            self.geometry(f"{self.hud_w}x{self.result_h}")
            self.btn_out_toggle.configure(fg_color="#0284C7")
        else:
            self.result_drawer.pack_forget()
            self.geometry(f"{self.hud_w}x{self.base_h}")
            self.btn_out_toggle.configure(fg_color="#1F2937")

    def _execute_from_palette(self, command_text: str):
        self.cmd_entry.delete(0, "end")
        self.cmd_entry.insert(0, command_text)
        # Close palette and run
        self.toggle_action_menu()
        self.on_execute()

    # ---------------- Command History ----------------
    def _on_history_up(self, event):
        if not self.cmd_history:
            return "break"
        if self.history_index < len(self.cmd_history) - 1:
            self.history_index += 1
            cmd = self.cmd_history[-(self.history_index + 1)]
            self.cmd_entry.delete(0, "end")
            self.cmd_entry.insert(0, cmd)
        return "break"

    def _on_history_down(self, event):
        if self.history_index > 0:
            self.history_index -= 1
            cmd = self.cmd_history[-(self.history_index + 1)]
            self.cmd_entry.delete(0, "end")
            self.cmd_entry.insert(0, cmd)
        elif self.history_index == 0:
            self.history_index = -1
            self.cmd_entry.delete(0, "end")
        return "break"

    # ---------------- Execution Pipeline ----------------
    def on_execute(self):
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            return

        if not self.cmd_history or self.cmd_history[-1] != cmd:
            self.cmd_history.append(cmd)
        self.history_index = -1
        self.cmd_entry.delete(0, "end")

        self.btn_send.configure(state="disabled", text="...")
        self.lbl_agent_badge.configure(text="⚡ Routing...", text_color="#F59E0B")
        self.lbl_route_type.configure(text="RUNNING", text_color="#F59E0B")

        threading.Thread(target=self._async_process, args=(cmd,), daemon=True).start()

    def _async_process(self, cmd: str):
        result: BrainResult = self.brain.process_command(cmd)
        self.after(0, lambda: self._update_ui_with_result(result))

    def _update_ui_with_result(self, result: BrainResult):
        theme = AGENT_THEMES.get(result.agent_id, {"icon": "🤖", "color": "#38BDF8", "label": result.agent_name})
        
        badge_text = f"{theme['icon']} {result.agent_name}"
        self.lbl_agent_badge.configure(text=badge_text, text_color=theme["color"])

        route_str = f"⚡ {result.execution_time_ms}ms" if result.is_fast_path else f"🧠 {result.execution_time_ms}ms"
        route_col = "#10B981" if result.is_fast_path else "#EC4899"
        self.lbl_route_type.configure(text=route_str, text_color=route_col)

        timestamp = time.strftime("%H:%M:%S")

        if isinstance(result.output, (dict, list)):
            out_str = json.dumps(result.output, indent=2)
        else:
            out_str = str(result.output)

        log_entry = f"[{timestamp}] > {result.command}\n{out_str}\n"

        self.output_box.insert("end", log_entry)
        self.output_box.see("end")

        # Open Result Drawer automatically if not open
        self.toggle_result_drawer(force_open=True)

        self.btn_send.configure(state="normal", text="RUN")

    def copy_output(self):
        text = self.output_box.get("1.0", "end-1c")
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.lbl_feed_title.configure(text="✓ Copied!", text_color="#10B981")
            self.after(1500, lambda: self.lbl_feed_title.configure(text="Execution Result", text_color="#94A3B8"))

    def clear_output(self):
        self.output_box.delete("1.0", "end")

    # ---------------- Background Telemetry Loop ----------------
    def _start_telemetry_loop(self):
        def _loop():
            while True:
                try:
                    import psutil
                    cpu_p = psutil.cpu_percent(interval=None)
                    ram_p = psutil.virtual_memory().percent
                    self.after(0, lambda c=cpu_p, r=ram_p: self._update_telemetry(c, r))
                except Exception:
                    pass
                time.sleep(2.0)

        threading.Thread(target=_loop, daemon=True).start()

    def _update_telemetry(self, cpu_val, ram_val):
        try:
            self.lbl_telemetry.configure(text=f"C:{cpu_val:.0f}% | R:{ram_val:.0f}%")
        except Exception:
            pass


def launch_ui():
    app = OrionBrainHUD()
    app.mainloop()


if __name__ == "__main__":
    launch_ui()

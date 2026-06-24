import tkinter as tk
import threading
import queue
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from brain.agent import Agent
from brain import tools as tool_module
from brain import morning_brief as mb
import voice.listener as listener
import voice.speaker as speaker

BG_DARK    = "#0f0f11"
BG_CARD    = "#1a1a1f"
BG_INPUT   = "#242429"
ACCENT     = "#7F77DD"
ACCENT_DIM = "#3C3489"
TEXT_PRI   = "#f0eff5"
TEXT_SEC   = "#9d9bab"
TEXT_HINT  = "#5c5a6b"
SUCCESS    = "#1D9E75"
WARNING    = "#EF9F27"
DANGER     = "#E24B4A"
BORDER     = "#2a2a33"

FONT_BODY  = ("Segoe UI", 11)
FONT_SMALL = ("Segoe UI", 9)
FONT_TITLE = ("Segoe UI", 13, "bold")


class AssistantApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.state = "normal"
        self.root.title(config.APP_NAME)
        self.root.geometry("780x680")
        self.root.minsize(620, 500)
        self.root.configure(bg=BG_DARK)

        self.agent = Agent()
        self.ui_queue = queue.Queue()
        self.is_listening = False
        self.is_processing = False

        self._build_ui()
        self._register_reminder_callback()
        self._poll_queue()

        # Escape key to stop speaking
        self.root.bind("<Escape>", lambda e: self._stop_speaking())

    def _build_ui(self):
        # Top bar
        topbar = tk.Frame(self.root, bg=BG_CARD, height=56)
        topbar.pack(fill=tk.X, side=tk.TOP)
        topbar.pack_propagate(False)

        tk.Label(topbar, text="◈ " + config.APP_NAME,
                 bg=BG_CARD, fg=TEXT_PRI, font=FONT_TITLE, padx=20).pack(side=tk.LEFT, pady=14)

        self.status_dot = tk.Label(topbar, text="●", bg=BG_CARD, fg=TEXT_HINT, font=("Segoe UI", 10))
        self.status_dot.pack(side=tk.RIGHT, padx=6)
        self.status_label = tk.Label(topbar, text="Ready", bg=BG_CARD, fg=TEXT_HINT, font=FONT_SMALL)
        self.status_label.pack(side=tk.RIGHT)

        tk.Button(topbar, text="Clear chat", bg=BG_CARD, fg=TEXT_SEC, relief=tk.FLAT,
                  font=FONT_SMALL, cursor="hand2", activebackground=BG_INPUT,
                  activeforeground=TEXT_PRI, command=self._clear_chat, padx=12
                  ).pack(side=tk.RIGHT, pady=12, padx=8)

        tk.Frame(self.root, bg=BORDER, height=1).pack(fill=tk.X)

        # Chat area
        chat_frame = tk.Frame(self.root, bg=BG_DARK)
        chat_frame.pack(fill=tk.BOTH, expand=True)

        self.chat_canvas = tk.Canvas(chat_frame, bg=BG_DARK, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(chat_frame, orient=tk.VERTICAL, command=self.chat_canvas.yview)
        self.chat_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.chat_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.chat_inner = tk.Frame(self.chat_canvas, bg=BG_DARK)
        self.chat_window = self.chat_canvas.create_window((0, 0), window=self.chat_inner, anchor="nw")

        self.chat_inner.bind("<Configure>", lambda e: self.chat_canvas.configure(
            scrollregion=self.chat_canvas.bbox("all")))
        self.chat_canvas.bind("<Configure>", lambda e: self.chat_canvas.itemconfig(
            self.chat_window, width=e.width))
        self.chat_canvas.bind("<MouseWheel>", lambda e: self.chat_canvas.yview_scroll(
            -1 * (e.delta // 120), "units"))

        self._add_system_message("Press 🎤 or type a message. Speak in any language!")
        self.root.after(800, self._start_morning_flow)

        # Bottom bar
        tk.Frame(self.root, bg=BORDER, height=1).pack(fill=tk.X)
        bottom = tk.Frame(self.root, bg=BG_CARD, pady=14)
        bottom.pack(fill=tk.X, side=tk.BOTTOM)

        self.mic_btn = tk.Button(bottom, text="🎤", font=("Segoe UI", 16),
                                  bg=ACCENT_DIM, fg=TEXT_PRI, relief=tk.FLAT,
                                  width=3, cursor="hand2",
                                  activebackground=ACCENT, activeforeground=TEXT_PRI,
                                  command=self._toggle_listen)
        self.mic_btn.pack(side=tk.LEFT, padx=(16, 8))

        self.text_input = tk.Entry(bottom, font=FONT_BODY, bg=BG_INPUT, fg=TEXT_PRI,
                                    insertbackground=ACCENT, relief=tk.FLAT, bd=0,
                                    highlightthickness=1, highlightbackground=BORDER,
                                    highlightcolor=ACCENT)
        self.text_input.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=(0, 8))
        self.text_input.bind("<Return>", self._on_send)

        self.send_btn = tk.Button(bottom, text="Send →", bg=ACCENT, fg=TEXT_PRI,
                                   relief=tk.FLAT, font=FONT_BODY, cursor="hand2",
                                   activebackground=ACCENT_DIM, activeforeground=TEXT_PRI,
                                   command=self._on_send, padx=16)
        self.send_btn.pack(side=tk.LEFT, ipady=9, padx=(0, 8))

        # Stop button
        self.stop_btn = tk.Button(bottom, text="⏹ Stop",
                                   bg="#3a1a1a", fg=DANGER, relief=tk.FLAT,
                                   font=FONT_BODY, cursor="hand2",
                                   activebackground=DANGER, activeforeground=TEXT_PRI,
                                   command=self._stop_speaking, padx=12)
        self.stop_btn.pack(side=tk.LEFT, ipady=9, padx=(0, 16))

    # ── Stop Speaking ─────────────────────────────────────────────────────────

    def _stop_speaking(self):
        speaker.stop()
        self.is_processing = False
        self.send_btn.config(state=tk.NORMAL)
        self.mic_btn.config(state=tk.NORMAL)
        self._set_status("Stopped.", TEXT_HINT)
        self._remove_typing_indicator()

    # ── Morning Brief ─────────────────────────────────────────────────────────

    def _start_morning_flow(self):
        if not mb.has_preferences():
            self._ask_for_topics()
        elif not mb.already_shown_today():
            self._show_morning_brief()
        else:
            self._add_system_message("Good to see you again! How can I help?")

    def _ask_for_topics(self):
        self.state = "asking_topics"
        question = ("🌅 Good morning! Before we begin —\n"
                    "What topics do you want in your daily morning brief?\n"
                    "Example: AI news, cricket, crypto, Pakistan tech...\n\n"
                    "Just type or speak!")
        self._add_brief_card(question)
        speaker.speak("Good morning! What topics would you like in your daily morning news brief?")

    def _show_morning_brief(self):
        self._add_system_message("☀️ Fetching your morning brief...")
        self._set_status("Loading morning brief...", WARNING)
        threading.Thread(target=self._generate_brief_thread, daemon=True).start()

    def _generate_brief_thread(self):
        prefs = mb.get_preferences()
        topics = prefs.get("topics", ["tech news"])
        lang = prefs.get("language", "en")
        try:
            brief = mb.generate_brief(topics, lang)
            mb.mark_shown_today()
            self.ui_queue.put(("morning_brief", brief, topics))
        except Exception as e:
            self.ui_queue.put(("morning_brief_error", str(e)))

    def _add_brief_card(self, text: str):
        outer = tk.Frame(self.chat_inner, bg=BG_DARK, pady=10)
        outer.pack(fill=tk.X, padx=16)
        header = tk.Frame(outer, bg="#12211a")
        header.pack(fill=tk.X)
        tk.Label(header, text=f"☀️ Morning Brief — {datetime.now().strftime('%B %d, %Y')}",
                 bg="#12211a", fg="#2ecc71",
                 font=("Segoe UI", 10, "bold"), padx=14, pady=8).pack(side=tk.LEFT)
        body = tk.Frame(outer, bg="#12211a", padx=14, pady=12)
        body.pack(fill=tk.X)
        tk.Message(body, text=text, bg="#12211a", fg=TEXT_PRI,
                   font=("Segoe UI", 12), relief=tk.FLAT, width=680,
                   justify=tk.LEFT).pack(fill=tk.X)
        tk.Frame(outer, bg="#2ecc71", height=2).pack(fill=tk.X)
        self.root.after(50, lambda: self.chat_canvas.yview_moveto(1.0))

    def _handle_topic_input(self, text: str):
        self._add_bubble(text, "user")
        self.state = "normal"
        def _save():
            topics = mb.extract_topics_from_message(text)
            mb.save_preferences(topics, "en")
            msg = f"Got it! Morning brief will cover: {', '.join(topics)}. Generating your first brief now..."
            self.ui_queue.put(("assistant_msg", msg))
            speaker.speak(msg)
            import time; time.sleep(1)
            self.ui_queue.put(("trigger_brief", None))
        threading.Thread(target=_save, daemon=True).start()

    # ── Chat UI ───────────────────────────────────────────────────────────────

    def _add_bubble(self, text: str, role: str, meta: str = ""):
        outer = tk.Frame(self.chat_inner, bg=BG_DARK, pady=6)
        outer.pack(fill=tk.X, padx=20)

        if role == "user":
            bubble_bg, text_col, align = ACCENT_DIM, TEXT_PRI, tk.RIGHT
            label_text, label_col = "You", ACCENT
        elif role == "assistant":
            bubble_bg, text_col, align = BG_CARD, TEXT_PRI, tk.LEFT
            label_text, label_col = "Assistant", SUCCESS
        else:
            bubble_bg, text_col, align = BG_INPUT, TEXT_SEC, tk.LEFT
            label_text, label_col = meta or "Tool", WARNING

        tk.Label(outer, text=label_text, bg=BG_DARK, fg=label_col,
                 font=("Segoe UI", 9, "bold")).pack(side=align)

        tk.Message(outer, text=text, bg=bubble_bg, fg=text_col,
                   font=FONT_BODY, relief=tk.FLAT, padx=14, pady=10,
                   width=560, justify=tk.LEFT).pack(side=align)

        if meta and role == "assistant":
            tk.Label(outer, text=meta, bg=BG_DARK, fg=TEXT_HINT,
                     font=("Segoe UI", 8)).pack(side=align)

        self.root.after(50, lambda: self.chat_canvas.yview_moveto(1.0))

    def _add_system_message(self, text: str):
        frame = tk.Frame(self.chat_inner, bg=BG_DARK, pady=10)
        frame.pack(fill=tk.X)
        tk.Label(frame, text=text, bg=BG_DARK, fg=TEXT_HINT,
                 font=FONT_SMALL, wraplength=500).pack()
        self.root.after(50, lambda: self.chat_canvas.yview_moveto(1.0))

    def _add_typing_indicator(self):
        self._typing_frame = tk.Frame(self.chat_inner, bg=BG_DARK, pady=6)
        self._typing_frame.pack(fill=tk.X, padx=20)
        tk.Label(self._typing_frame, text="Assistant", bg=BG_DARK, fg=SUCCESS,
                 font=("Segoe UI", 9, "bold")).pack(anchor=tk.W)
        self._typing_label = tk.Label(self._typing_frame, text="Thinking...",
                                       bg=BG_CARD, fg=TEXT_HINT, font=FONT_BODY, padx=14, pady=10)
        self._typing_label.pack(anchor=tk.W)
        self.root.after(50, lambda: self.chat_canvas.yview_moveto(1.0))

    def _remove_typing_indicator(self):
        if hasattr(self, "_typing_frame"):
            self._typing_frame.destroy()

    def _set_status(self, text: str, color: str = TEXT_HINT):
        self.status_label.config(text=text, fg=color)
        self.status_dot.config(fg=color)

    # ── Input ─────────────────────────────────────────────────────────────────

    def _on_send(self, event=None):
        text = self.text_input.get().strip()
        if not text or self.is_processing:
            return
        self.text_input.delete(0, tk.END)
        if self.state == "asking_topics":
            self._handle_topic_input(text)
        else:
            self._process_input(text)

    def _clear_chat(self):
        for widget in self.chat_inner.winfo_children():
            widget.destroy()
        self.agent.clear_history()
        self._add_system_message("Chat cleared. Start a new conversation.")

    def _toggle_listen(self):
        if self.is_listening or self.is_processing:
            return
        threading.Thread(target=self._listen_thread, daemon=True).start()

    def _listen_thread(self):
        self.is_listening = True
        self.ui_queue.put(("status", "Listening...", ACCENT))
        self.ui_queue.put(("mic_active", True))

        try:
            text = listener.listen(
                on_speaking=lambda: self.ui_queue.put(("status", "Speaking detected...", SUCCESS)),
                on_silence=lambda: self.ui_queue.put(("status", "Processing speech...", WARNING))
            )
        except Exception as e:
            self.ui_queue.put(("status", f"Mic error: {e}", DANGER))
            text = ""
        finally:
            self.is_listening = False
            self.ui_queue.put(("mic_active", False))

        if text:
            if self.state == "asking_topics":
                self.ui_queue.put(("topic_input", text))
            else:
                self.ui_queue.put(("process", text))
        else:
            self.ui_queue.put(("status", "Nothing heard. Try again.", TEXT_HINT))

    def _process_input(self, text: str):
        self.is_processing = True
        self._set_status("Processing...", WARNING)
        self.send_btn.config(state=tk.DISABLED)
        self.mic_btn.config(state=tk.DISABLED)
        self._add_bubble(text, "user")
        self._add_typing_indicator()
        threading.Thread(target=self._agent_thread, args=(text,), daemon=True).start()

    def _agent_thread(self, text: str):
        def on_tool_call(name, inputs):
            label = f"Searching: {inputs.get('query', '')}" if name == "web_search" else f"Tool: {name}"
            self.ui_queue.put(("tool_msg", label, name))

        try:
            reply = self.agent.chat(text, on_tool_call=on_tool_call)
        except Exception as e:
            reply = f"Sorry, I ran into an error: {str(e)}"

        timestamp = datetime.now().strftime("%I:%M %p")
        self.ui_queue.put(("reply", reply, timestamp))

        speaker.speak(
            reply,
            on_start=lambda: self.ui_queue.put(("status", "Speaking...", SUCCESS)),
            on_done=lambda: (
                self.ui_queue.put(("status", "Ready", TEXT_HINT)),
                self.ui_queue.put(("enable_input", None)),
                setattr(self, "is_processing", False)
            )
        )

    # ── Queue ─────────────────────────────────────────────────────────────────

    def _poll_queue(self):
        try:
            while True:
                item = self.ui_queue.get_nowait()
                cmd = item[0]
                if cmd == "status":
                    self._set_status(item[1], item[2])
                elif cmd == "mic_active":
                    self.mic_btn.config(bg=DANGER if item[1] else ACCENT_DIM,
                                        text="⬛" if item[1] else "🎤")
                elif cmd == "process":
                    self._process_input(item[1])
                elif cmd == "topic_input":
                    self._handle_topic_input(item[1])
                elif cmd == "assistant_msg":
                    self._add_bubble(item[1], "assistant")
                elif cmd == "tool_msg":
                    self._add_bubble(item[1], "tool", item[2])
                elif cmd == "reply":
                    self._remove_typing_indicator()
                    self._add_bubble(item[1], "assistant", item[2])
                elif cmd == "enable_input":
                    self.send_btn.config(state=tk.NORMAL)
                    self.mic_btn.config(state=tk.NORMAL)
                elif cmd == "morning_brief":
                    brief_text, topics = item[1], item[2]
                    self._add_brief_card(brief_text)
                    self._set_status("Ready", TEXT_HINT)
                    self.state = "normal"
                    self._add_system_message(f"Topics: {', '.join(topics)} · Say 'change my brief topics' to update")
                    speaker.speak(brief_text)
                elif cmd == "morning_brief_error":
                    self._add_system_message(f"Could not load brief: {item[1]}")
                elif cmd == "trigger_brief":
                    self._show_morning_brief()
                elif cmd == "reminder_fire":
                    self._add_system_message(f"⏰ Reminder: {item[1]}")
                    speaker.speak(f"Reminder: {item[1]}")
        except queue.Empty:
            pass
        self.root.after(50, self._poll_queue)

    def _register_reminder_callback(self):
        tool_module.register_reminder_callback(
            lambda msg: self.ui_queue.put(("reminder_fire", msg))
        )


def main():
    root = tk.Tk()
    AssistantApp(root)
    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()

if __name__ == "__main__":
    main()
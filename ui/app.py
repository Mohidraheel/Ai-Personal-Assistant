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

        self._add_system_message("Press 🎤 or type a message to begin.")

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
        self.send_btn.pack(side=tk.LEFT, ipady=9, padx=(0, 16))

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

    def _on_send(self, event=None):
        text = self.text_input.get().strip()
        if not text or self.is_processing:
            return
        self.text_input.delete(0, tk.END)
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
                elif cmd == "tool_msg":
                    self._add_bubble(item[1], "tool", item[2])
                elif cmd == "reply":
                    self._remove_typing_indicator()
                    self._add_bubble(item[1], "assistant", item[2])
                elif cmd == "enable_input":
                    self.send_btn.config(state=tk.NORMAL)
                    self.mic_btn.config(state=tk.NORMAL)
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

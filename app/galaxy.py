#!/usr/bin/env python3
"""Wah-Lah Galaxy — a guarded GUI for the strict free-model AI lab.

The only model is read from config/models.json. This UI never silently changes it.
File writes and CLI code checks require explicit GUI approval.
"""
from __future__ import annotations
import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import wave
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, filedialog
import lab as backend

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = (ROOT / backend.SETTINGS["workspace"]).resolve()
MODEL = backend.MODEL
BG = "#070914"
PANEL = "#10172a"
PANEL2 = "#151f38"
BORDER = "#253456"
CYAN = "#49f2dc"
PURPLE = "#a78bfa"
GOLD = "#f6cc79"
TEXT = "#f2f6ff"
MUTED = "#a3b2ce"
GREEN = "#7fe0ad"
RED = "#ff8b9c"
VOICE_MODEL = Path.home() / ".local/share/vosk-models/small-en"
MIC_SOURCE = "android-87f1610"

class GalaxyApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Wah-Lah Galaxy | Free Uncensored AI Lab")
        self.root.geometry("1360x860")
        self.root.minsize(1050, 700)
        self.root.configure(bg=BG)
        self.uiq: queue.Queue = queue.Queue()
        self.messages = [{"role": "system", "content": backend.SYSTEM}]
        self.busy = False
        self.last_response = ""
        self.last_model_check = False
        self.voice_model = None
        self.voice_model_lock = threading.Lock()
        self.voice_on = tk.BooleanVar(value=bool(backend.SETTINGS.get("voice_output_default", True)))
        self.status_var = tk.StringVar(value="CONNECTING TO FREE MODEL ROUTE…")
        self.page_name = "CHAT"
        self.pages = {}
        self.key = self.load_key()
        self.build_shell()
        self.show_page("CHAT")
        self.root.after(100, self.poll_queue)
        self.root.after(250, self.initial_check)

    def load_key(self):
        try:
            if backend.KEYFILE.is_file():
                value = backend.KEYFILE.read_text().strip()
                if value:
                    try:
                        os.chmod(backend.KEYFILE, 0o600)
                    except OSError:
                        pass
                    return value
        except OSError:
            pass
        return None

    def build_shell(self):
        header = tk.Canvas(self.root, bg=BG, height=156, highlightthickness=0)
        header.pack(fill="x")
        header.configure(height=156)
        # Fixed constellation field: light decoration only, no network or animation.
        import random
        rng = random.Random(2401)
        width = 1360
        for _ in range(118):
            x = rng.randint(5, width - 5)
            y = rng.randint(5, 148)
            r = rng.choice([1, 1, 1, 2])
            color = rng.choice(["#344664", "#536687", "#49a9b9", "#7663bb"])
            header.create_oval(x-r, y-r, x+r, y+r, fill=color, outline="")
        header.create_oval(1040, -82, 1242, 120, outline="#244a64", width=2)
        header.create_oval(1072, -47, 1208, 89, outline="#3a3470", width=2)
        header.create_oval(1095, -23, 1185, 67, outline="#3a8f91", width=1)
        header.create_oval(1135, 16, 1145, 26, fill=CYAN, outline="")
        header.create_line(1048, 25, 1140, 21, fill="#2f687b", width=1)
        header.create_line(1140, 21, 1224, 60, fill="#4f457a", width=1)
        header.create_text(36, 34, anchor="w", text="W A H - L A H   /   G A L A X Y", fill=CYAN,
                           font=("DejaVu Sans", 10, "bold"))
        header.create_text(34, 70, anchor="w", text="UNCENSORED INTELLIGENCE LAB", fill=TEXT,
                           font=("DejaVu Sans", 25, "bold"))
        header.create_text(36, 108, anchor="w",
                           text="Free model • strict allowlist • voice • coding tools • your PC stays yours",
                           fill=MUTED, font=("DejaVu Sans", 10))
        header.create_text(36, 137, anchor="w",
                           text="HERMES 3 / LLAMA 3.1 405B  |  NO AUTO-FALLBACK  |  WORKSPACE-ONLY WRITES",
                           fill=GOLD, font=("DejaVu Sans Mono", 9, "bold"))

        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=(0, 10))
        nav = tk.Frame(body, bg=PANEL, width=212, highlightbackground=BORDER, highlightthickness=1)
        nav.pack(side="left", fill="y", padx=(0, 14))
        nav.pack_propagate(False)
        tk.Label(nav, text="COMMAND DECK", bg=PANEL, fg=MUTED,
                 font=("DejaVu Sans", 9, "bold")).pack(anchor="w", padx=18, pady=(22, 12))
        self.nav_buttons = {}
        for label, subtitle in [
            ("CHAT", "Talk to the model"),
            ("WORKSPACE", "Code and files"),
            ("TOOLS", "Guarded operations"),
            ("MODEL CORE", "Policy and status"),
        ]:
            b = tk.Button(nav, text=label + "\n" + subtitle, anchor="w", justify="left",
                          command=lambda name=label: self.show_page(name),
                          bg=PANEL2, fg=TEXT, activebackground="#20304d", activeforeground=CYAN,
                          relief="flat", bd=0, padx=14, pady=12,
                          font=("DejaVu Sans", 10, "bold"), cursor="hand2")
            b.pack(fill="x", padx=10, pady=4)
            self.nav_buttons[label] = b
        tk.Frame(nav, bg=BORDER, height=1).pack(fill="x", padx=14, pady=(18, 12))
        tk.Label(nav, text="ACTIVE MODEL", bg=PANEL, fg=MUTED,
                 font=("DejaVu Sans", 8, "bold")).pack(anchor="w", padx=18)
        tk.Label(nav, text="HERMES 3\n405B", bg=PANEL, fg=CYAN, justify="left",
                 font=("DejaVu Sans", 19, "bold")).pack(anchor="w", padx=18, pady=(5, 0))
        tk.Label(nav, text="Free route • fixed ID\nNo paid fallback", bg=PANEL, fg=GOLD, justify="left",
                 font=("DejaVu Sans", 9)).pack(anchor="w", padx=18, pady=(4, 12))
        tk.Label(nav, text="POWER BOUNDARIES", bg=PANEL, fg=MUTED,
                 font=("DejaVu Sans", 8, "bold")).pack(anchor="w", padx=18)
        for txt in ("✓ No arbitrary shell", "✓ Workspace-only files", "✓ Approve each write", "✓ CLI sandbox + timeout"):
            tk.Label(nav, text=txt, bg=PANEL, fg=GREEN,
                     font=("DejaVu Sans", 8)).pack(anchor="w", padx=18, pady=3)
        tk.Button(nav, text="OPEN WORKSPACE FOLDER", command=self.open_workspace,
                  bg="#1c2a42", fg=CYAN, activebackground="#223854", relief="flat", bd=0,
                  padx=9, pady=9, font=("DejaVu Sans", 8, "bold"), cursor="hand2").pack(
                      side="bottom", fill="x", padx=10, pady=12)

        self.content = tk.Frame(body, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)
        footer = tk.Frame(self.root, bg="#0b1020", highlightbackground=BORDER, highlightthickness=1)
        footer.pack(fill="x", side="bottom")
        tk.Label(footer, text="●", bg="#0b1020", fg=CYAN,
                 font=("DejaVu Sans", 9)).pack(side="left", padx=(14, 5), pady=8)
        tk.Label(footer, textvariable=self.status_var, bg="#0b1020", fg=MUTED,
                 font=("DejaVu Sans Mono", 9), anchor="w").pack(side="left", fill="x", expand=True, pady=8)
        tk.Label(footer, text="PERMISSIONS: EXPLICIT", bg="#0b1020", fg=GOLD,
                 font=("DejaVu Sans Mono", 8, "bold")).pack(side="right", padx=14)

        self.build_chat_page()
        self.build_workspace_page()
        self.build_tools_page()
        self.build_model_page()

    def make_card(self, parent, title, note=None):
        card = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        if title:
            tk.Label(card, text=title, bg=PANEL, fg=TEXT,
                     font=("DejaVu Sans", 13, "bold")).pack(anchor="w", padx=15, pady=(13, 3))
        if note:
            tk.Label(card, text=note, bg=PANEL, fg=MUTED, anchor="w", justify="left",
                     font=("DejaVu Sans", 9)).pack(anchor="w", padx=15, pady=(0, 10))
        return card

    def make_button(self, parent, text, command, accent=CYAN):
        return tk.Button(parent, text=text, command=command, bg="#1b2943", fg=accent,
                         activebackground="#2c3c5d", activeforeground=TEXT,
                         relief="flat", bd=0, padx=14, pady=9,
                         font=("DejaVu Sans", 9, "bold"), cursor="hand2")

    def build_chat_page(self):
        page = tk.Frame(self.content, bg=BG)
        self.pages["CHAT"] = page
        intro = tk.Frame(page, bg=BG)
        intro.pack(fill="x", pady=(3, 10))
        tk.Label(intro, text="THE CONVERSATION", bg=BG, fg=TEXT,
                 font=("DejaVu Sans", 17, "bold")).pack(side="left")
        tk.Label(intro, text="DIRECT • TOOL-AWARE • NO MODEL SWITCHING", bg=BG, fg=CYAN,
                 font=("DejaVu Sans Mono", 8, "bold")).pack(side="right", pady=5)
        card = self.make_card(page, "", "Ask for code, debugging, research, ideas, writing, or explanations. Tools run only inside the permissions shown here.")
        card.pack(fill="both", expand=True)
        transcript_frame = tk.Frame(card, bg=PANEL)
        transcript_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self.transcript = tk.Text(transcript_frame, wrap="word", state="disabled",
                                  bg="#0a1020", fg=TEXT, insertbackground=CYAN,
                                  selectbackground="#2c4a69", relief="flat", bd=0,
                                  font=("DejaVu Sans", 10), padx=14, pady=12,
                                  spacing1=3, spacing3=6)
        scroll = tk.Scrollbar(transcript_frame, command=self.transcript.yview)
        self.transcript.configure(yscrollcommand=scroll.set)
        self.transcript.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.transcript.tag_configure("user", foreground=CYAN, font=("DejaVu Sans", 10, "bold"))
        self.transcript.tag_configure("assistant", foreground=TEXT)
        self.transcript.tag_configure("system", foreground=GOLD, font=("DejaVu Sans Mono", 9))
        self.transcript.tag_configure("error", foreground=RED)
        self.transcript.tag_configure("meta", foreground=MUTED, font=("DejaVu Sans Mono", 8))
        self.append_transcript("system",
            "GALAXY ONLINE / model target: " + MODEL +
            "\nOpenRouter exact :free route only. Send stays locked until $0 endpoint verification succeeds. Writes and CLI execution require approval.")
        compose = tk.Frame(card, bg=PANEL)
        compose.pack(fill="x", padx=12, pady=(0, 12))
        self.input = tk.Text(compose, height=3, wrap="word", bg="#111a2d", fg=TEXT,
                             insertbackground=CYAN, relief="flat", bd=0,
                             font=("DejaVu Sans", 10), padx=10, pady=9)
        self.input.pack(fill="x", pady=(0, 8))
        self.input.bind("<Control-Return>", self.send_shortcut)
        controls = tk.Frame(compose, bg=PANEL)
        controls.pack(fill="x")
        self.send_button = self.make_button(controls, "SEND TO GALAXY  ↗", self.send_message, CYAN)
        self.send_button.pack(side="left")
        self.send_button.configure(state="disabled")
        self.listen_button = self.make_button(controls, "LISTEN · G8 MIC · 8 SEC", self.listen, PURPLE)
        self.listen_button.pack(side="left", padx=(8, 0))
        self.speak_button = self.make_button(controls, "SPEAK LAST ANSWER", self.speak_last, GOLD)
        self.speak_button.pack(side="left", padx=(8, 0))
        tk.Checkbutton(controls, text="Speak replies", variable=self.voice_on,
                       bg=PANEL, fg=MUTED, selectcolor="#111a2d", activebackground=PANEL,
                       activeforeground=TEXT, font=("DejaVu Sans", 9)).pack(side="right")
        self.set_status("MODEL CHECK PENDING / SEND LOCKED UNTIL EXACT $0 ROUTE IS VERIFIED")

    def build_workspace_page(self):
        page = tk.Frame(self.content, bg=BG)
        self.pages["WORKSPACE"] = page
        tk.Label(page, text="THE WORKSHOP", bg=BG, fg=TEXT,
                 font=("DejaVu Sans", 17, "bold")).pack(anchor="w", pady=(3, 5))
        tk.Label(page, text="The agent's file permissions stop at this folder. Use the editor to inspect files; saves require confirmation.",
                 bg=BG, fg=MUTED, font=("DejaVu Sans", 9)).pack(anchor="w", pady=(0, 10))
        top = tk.Frame(page, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        top.pack(fill="x", pady=(0, 10))
        self.workspace_path_label = tk.Label(top, text=str(WORKSPACE), bg=PANEL, fg=CYAN,
                                             font=("DejaVu Sans Mono", 8), anchor="w")
        self.workspace_path_label.pack(side="left", padx=12, pady=12, fill="x", expand=True)
        self.make_button(top, "REFRESH FILES", self.refresh_workspace).pack(side="right", padx=7, pady=6)
        content = tk.Frame(page, bg=BG)
        content.pack(fill="both", expand=True)
        left = tk.Frame(content, bg=PANEL, width=250, highlightbackground=BORDER, highlightthickness=1)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)
        tk.Label(left, text="WORKSPACE FILES", bg=PANEL, fg=MUTED,
                 font=("DejaVu Sans", 8, "bold")).pack(anchor="w", padx=12, pady=(12, 7))
        self.file_list = tk.Listbox(left, bg="#0a1020", fg=TEXT, selectbackground="#27435f",
                                    selectforeground=CYAN, relief="flat", bd=0,
                                    font=("DejaVu Sans Mono", 9), activestyle="dotbox")
        self.file_list.pack(fill="both", expand=True, padx=8, pady=(0, 10))
        self.file_list.bind("<<ListboxSelect>>", self.load_selected_file)
        self.current_file = tk.StringVar(value="")
        right = tk.Frame(content, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        right.pack(side="left", fill="both", expand=True)
        name_bar = tk.Frame(right, bg=PANEL)
        name_bar.pack(fill="x", padx=10, pady=8)
        tk.Label(name_bar, text="RELATIVE PATH", bg=PANEL, fg=MUTED,
                 font=("DejaVu Sans Mono", 8)).pack(side="left")
        self.file_path_entry = tk.Entry(name_bar, textvariable=self.current_file, bg="#0a1020", fg=CYAN,
                                        insertbackground=CYAN, relief="flat", bd=0,
                                        font=("DejaVu Sans Mono", 9))
        self.file_path_entry.pack(side="left", fill="x", expand=True, padx=(8, 0), ipady=5)
        self.editor = tk.Text(right, wrap="none", bg="#0a1020", fg=TEXT, insertbackground=CYAN,
                              selectbackground="#27435f", relief="flat", bd=0,
                              font=("DejaVu Sans Mono", 9), padx=10, pady=10, undo=True)
        self.editor.pack(fill="both", expand=True, padx=10)
        buttons = tk.Frame(right, bg=PANEL)
        buttons.pack(fill="x", padx=10, pady=10)
        self.make_button(buttons, "SAVE WITH APPROVAL", self.save_editor, GOLD).pack(side="left")
        self.make_button(buttons, "NEW FILE", self.new_workspace_file, CYAN).pack(side="left", padx=8)
        self.make_button(buttons, "OPEN FOLDER", self.open_workspace, PURPLE).pack(side="right")
        self.refresh_workspace()

    def build_tools_page(self):
        page = tk.Frame(self.content, bg=BG)
        self.pages["TOOLS"] = page
        tk.Label(page, text="GUARDED OPERATIONS", bg=BG, fg=TEXT,
                 font=("DejaVu Sans", 17, "bold")).pack(anchor="w", pady=(3, 5))
        tk.Label(page, text="No general-purpose shell. The CLI is a fixed list of operations, sandboxed with networking disabled.",
                 bg=BG, fg=MUTED, font=("DejaVu Sans", 9)).pack(anchor="w", pady=(0, 12))
        row = tk.Frame(page, bg=BG)
        row.pack(fill="x")
        card1 = self.make_card(row, "CONNECTION", "Check the current free endpoint and the fixed model ID.")
        card1.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.make_button(card1, "TEST FREE MODEL", self.check_model, CYAN).pack(anchor="w", padx=15, pady=(2, 15))
        card2 = self.make_card(row, "WORKSPACE", "List workspace files or open the folder in the file manager.")
        card2.pack(side="left", fill="both", expand=True, padx=(8, 0))
        self.make_button(card2, "LIST FILES", self.refresh_workspace).pack(anchor="w", padx=15, pady=(2, 15))
        self.make_button(card2, "OPEN FOLDER", self.open_workspace, PURPLE).pack(anchor="w", padx=15, pady=(0, 15))
        cli = self.make_card(page, "CLI CHECKS", "Only the operations below are allowed. Anything that executes code requires explicit approval.")
        cli.pack(fill="x", pady=(12, 10))
        self.cli_path = tk.StringVar(value="")
        r = tk.Frame(cli, bg=PANEL)
        r.pack(fill="x", padx=15, pady=(2, 8))
        tk.Label(r, text="Workspace-relative file/test path:", bg=PANEL, fg=MUTED,
                 font=("DejaVu Sans", 9)).pack(side="left")
        tk.Entry(r, textvariable=self.cli_path, bg="#0a1020", fg=CYAN, insertbackground=CYAN,
                 relief="flat", bd=0, font=("DejaVu Sans Mono", 9), width=34).pack(side="left", padx=8, ipady=5)
        ops = tk.Frame(cli, bg=PANEL)
        ops.pack(fill="x", padx=15, pady=(0, 14))
        for label, op in [("PYTHON SYNTAX", "python_check"), ("NODE SYNTAX", "node_check"),
                          ("PYTEST", "pytest"), ("GIT STATUS", "git_status"),
                          ("GIT DIFF CHECK", "git_diff_check")]:
            self.make_button(ops, label, lambda name=op: self.run_cli(name), PURPLE).pack(side="left", padx=(0, 7))
        log_card = self.make_card(page, "OPERATION FEED", "Shows this session's tool results. Prompts and credentials are not written to logs.")
        log_card.pack(fill="both", expand=True)
        self.tool_feed = tk.Text(log_card, height=8, bg="#0a1020", fg=TEXT, state="disabled",
                                 wrap="word", relief="flat", bd=0, font=("DejaVu Sans Mono", 9), padx=10, pady=8)
        self.tool_feed.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def build_model_page(self):
        page = tk.Frame(self.content, bg=BG)
        self.pages["MODEL CORE"] = page
        tk.Label(page, text="MODEL CORE / PERMISSIONS", bg=BG, fg=TEXT,
                 font=("DejaVu Sans", 17, "bold")).pack(anchor="w", pady=(3, 12))
        model = self.make_card(page, "HERMES 3 · LLAMA 3.1 · 405B", "The only model this app may call.")
        model.pack(fill="x", pady=(0, 10))
        tk.Label(model, text=MODEL, bg=PANEL, fg=CYAN, font=("DejaVu Sans Mono", 11, "bold")).pack(anchor="w", padx=15, pady=(2, 14))
        notes = self.make_card(page, "STRICT ROUTING POLICY")
        notes.pack(fill="x", pady=(0, 10))
        for line in [
            "Inference API: " + backend.SETTINGS["api_base_url"],
            "Existing FreeLLMAPI health: " + backend.SETTINGS["ping_url"],
            "A single, exact model ID is allowlisted. There is no auto model-selection.",
            "Live status: the exact :free model currently returns HTTP 404; Send remains locked until it is explicitly verified at $0.",
            "If the model is unavailable, the app stops; it does not switch to a paid or ordinary model.",
            "This lab uses one exact OpenRouter :free model ID; no auto routing or model fallback.",
            "OpenRouter key: .secrets/openrouter-api-key (owner-only permissions, 0600).",
            "The pre-existing FreeLLMAPI model catalog currently has large models disabled/needsKey; its service was not reconfigured.",
        ]:
            tk.Label(notes, text="• " + line, bg=PANEL, fg=TEXT, anchor="w", justify="left",
                     wraplength=780, font=("DejaVu Sans", 9)).pack(fill="x", padx=15, pady=4)
        perms = self.make_card(page, "THE MODEL HAS HANDS, NOT ROOT")
        perms.pack(fill="x", pady=(0, 10))
        for line in [
            "Workspace reads/writes stop at workspace/. Every write requires your confirmation.",
            "Code checks run only through bubblewrap: no network, no home directory, workspace is the only writable mount, 30-second timeout.",
            "No service control, broad file-system search, package installation, or general shell is exposed.",
            "Voice uses the existing G8 microphone source only when you press Listen. Speech output uses local spd-say.",
        ]:
            tk.Label(perms, text="• " + line, bg=PANEL, fg=TEXT, anchor="w", justify="left",
                     wraplength=780, font=("DejaVu Sans", 9)).pack(fill="x", padx=15, pady=4)
        self.make_button(page, "VERIFY CONNECTION AND MODEL", self.check_model, CYAN).pack(anchor="w", pady=6)

    def show_page(self, name):
        self.page_name = name
        for page in self.pages.values():
            page.pack_forget()
        self.pages[name].pack(fill="both", expand=True)
        for label, btn in self.nav_buttons.items():
            btn.configure(bg="#20334d" if label == name else PANEL2,
                          fg=CYAN if label == name else TEXT)
        self.set_status(name + " / " + MODEL)

    def set_status(self, text):
        self.status_var.set(str(text)[:220])

    def append_transcript(self, role, text):
        tag = role if role in ("user", "assistant", "system", "error", "meta") else "system"
        if not hasattr(self, "transcript"):
            return
        self.transcript.configure(state="normal")
        labels = {"user": "YOU", "assistant": "HERMES 3 / 405B", "system": "GALAXY",
                  "error": "BLOCKED / ERROR", "meta": "TOOL"}
        self.transcript.insert("end", "\n" + labels.get(tag, "GALAXY") + "\n", tag)
        self.transcript.insert("end", str(text).rstrip() + "\n", tag)
        self.transcript.configure(state="disabled")
        self.transcript.see("end")

    def feed(self, text, error=False):
        if not hasattr(self, "tool_feed"):
            return
        self.tool_feed.configure(state="normal")
        prefix = "BLOCKED / " if error else "• "
        self.tool_feed.insert("end", prefix + str(text).rstrip() + "\n")
        self.tool_feed.see("end")
        self.tool_feed.configure(state="disabled")

    def initial_check(self):
        if not self.key:
            self.set_status("CLIENT KEY MISSING — use ./launch.sh --setup-key")
            self.append_transcript("error", "No OpenRouter API key is saved. The GUI will not collect keys in plain text; run ./launch.sh --setup-key from the folder for hidden input.")
            return
        threading.Thread(target=self.model_check_worker, daemon=True).start()

    def check_model(self):
        if not self.key:
            messagebox.showerror("Client key missing", "Run ./launch.sh --setup-key from the app folder first.", parent=self.root)
            return
        if self.busy:
            return
        self.set_status("VERIFYING FREE ROUTE AND EXACT MODEL…")
        self.feed("Starting authenticated model availability check.")
        threading.Thread(target=self.model_check_worker, daemon=True).start()

    def model_check_worker(self):
        try:
            backend.check_service()
            backend.verify_model(self.key)
            self.last_model_check = True
            self.uiq.put(("model_check_done", True))
            self.uiq.put(("status", "VERIFIED / EXACT :FREE MODEL / $0 / NO FALLBACK"))
            self.uiq.put(("feed", "OpenRouter confirms the exact allowlisted Hermes 3 model and $0 pricing; fallback remains disabled. FreeLLMAPI health was checked separately.", False))
        except Exception as exc:
            self.last_model_check = False
            self.uiq.put(("model_check_done", False))
            self.uiq.put(("status", "MODEL CHECK FAILED — NO FALLBACK SELECTED"))
            self.uiq.put(("feed", str(exc), True))

    def send_shortcut(self, _event):
        self.send_message()
        return "break"

    def send_message(self):
        if self.busy:
            return
        text = self.input.get("1.0", "end").strip()
        if not text:
            return
        if not self.key:
            messagebox.showerror("Client key missing", "Run ./launch.sh --setup-key from the app folder first.", parent=self.root)
            return
        if not self.last_model_check:
            messagebox.showerror("Free model unavailable", "The exact $0 Hermes 3 405B endpoint has not passed verification. No message was sent. Press TEST FREE MODEL to retry; the app will not switch to a paid or different model.", parent=self.root)
            return
        self.input.delete("1.0", "end")
        self.messages.append({"role": "user", "content": text})
        self.append_transcript("user", text)
        self.busy = True
        self.send_button.configure(state="disabled")
        self.set_status("HERMES 3 / THINKING WITH THE FIXED MODEL…")
        threading.Thread(target=self.chat_worker, daemon=True).start()

    def ask_approval(self, title, details):
        event = threading.Event()
        result = {}
        self.uiq.put(("approval", title, details, event, result))
        if not event.wait(300):
            return False
        return bool(result.get("approved"))

    def do_workspace_write(self, args):
        path = backend.safe_path(args.get("path", ""), missing=True)
        content = args.get("content", "")
        if not isinstance(content, str) or len(content.encode("utf-8")) > 200000:
            raise ValueError("Workspace file writes must be text and no larger than 200 KB.")
        if path.exists() and not path.is_file():
            raise ValueError("The target path is not a regular file.")
        details = "The model proposes a workspace file write.\n\nPath: " + str(path.relative_to(WORKSPACE)) + "\nBytes: " + str(len(content.encode("utf-8")))
        if path.exists():
            details += "\n\nAn existing file will be replaced."
        if not self.ask_approval("Approve model file write?", details):
            return {"approved": False, "message": "You declined the write; no file was changed."}
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"approved": True, "path": str(path.relative_to(WORKSPACE)), "bytes_written": path.stat().st_size}

    def do_cli(self, args):
        op = args.get("operation")
        rel = args.get("path", "")
        cwd = backend.safe_path(args.get("cwd", "."))
        if not cwd.is_dir():
            raise ValueError("CLI working directory must be a workspace directory.")
        if op == "list":
            return backend.t_list({"path": rel or "."})
        if op == "python_check":
            p = backend.safe_path(rel)
            if not p.is_file() or p.suffix != ".py":
                raise ValueError("python_check requires an existing .py workspace file.")
            argv = ["/usr/bin/python3", "-I", "-m", "py_compile", "/workspace/" + str(p.relative_to(WORKSPACE))]
        elif op == "node_check":
            p = backend.safe_path(rel)
            if not p.is_file() or p.suffix not in (".js", ".mjs", ".cjs"):
                raise ValueError("node_check requires an existing .js, .mjs or .cjs workspace file.")
            node = shutil.which("node")
            if not node:
                raise RuntimeError("Node.js is not installed; no package was installed.")
            if not Path(node).is_relative_to(Path("/usr")) and not Path(node).is_relative_to(Path("/bin")):
                raise RuntimeError("Node.js is outside the read-only sandbox runtime; failing closed.")
            argv = [node, "--check", "/workspace/" + str(p.relative_to(WORKSPACE))]
        elif op == "pytest":
            pytest = Path("/usr/bin/pytest")
            if not pytest.is_file():
                raise RuntimeError("System pytest is not installed; no package was installed.")
            argv = [str(pytest), "-q"]
            if rel:
                p = backend.safe_path(rel)
                argv.append("/workspace/" + str(p.relative_to(WORKSPACE)))
        elif op in ("git_status", "git_diff_check"):
            if not ((cwd / ".git").exists() or (cwd / ".git").is_file()):
                raise RuntimeError("No Git repository found in the selected workspace directory.")
            argv = ["/usr/bin/git", "status", "--short", "--", "."] if op == "git_status" else ["/usr/bin/git", "diff", "--check", "--", "."]
        else:
            raise ValueError("CLI operation not allowlisted.")
        command = " ".join(argv)
        details = "This fixed CLI operation will run in an isolated sandbox.\n\nOperation: " + str(op)
        details += "\nWorking directory: " + (str(cwd.relative_to(WORKSPACE)) or ".")
        details += "\nCommand: " + command
        details += "\n\nNetwork disabled. No home directory. Only workspace/ writable. Timeout: 30 seconds."
        if not self.ask_approval("Approve sandboxed CLI run?", details):
            return {"approved": False, "message": "You declined; command was not run."}
        bwrap = shutil.which("bwrap")
        if not bwrap:
            raise RuntimeError("bubblewrap is not available; failing closed.")
        sandbox = [bwrap, "--unshare-all", "--die-with-parent", "--ro-bind", "/usr", "/usr", "--ro-bind", "/bin", "/bin"]
        for path in ("/lib", "/lib64"):
            if Path(path).exists():
                sandbox += ["--ro-bind", path, path]
        sandbox += ["--ro-bind", "/etc", "/etc", "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
                    "--bind", str(WORKSPACE), "/workspace"]
        dest = "/workspace" if cwd == WORKSPACE else "/workspace/" + str(cwd.relative_to(WORKSPACE))
        sandbox += ["--chdir", dest] + argv
        env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp", "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}
        try:
            proc = subprocess.run(sandbox, cwd=str(WORKSPACE), env=env, text=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30, check=False)
            return {"operation": op, "exit_code": proc.returncode, "output": proc.stdout[-10000:],
                    "sandbox": "bubblewrap / network disabled / workspace only writable"}
        except subprocess.TimeoutExpired as exc:
            output = exc.stdout or ""
            if isinstance(output, bytes):
                output = output.decode("utf-8", "replace")
            return {"operation": op, "timed_out": True, "timeout_seconds": 30, "output": output[-10000:]}

    def chat_worker(self):
        try:
            backend.verify_model(self.key)
            for round_no in range(int(backend.SETTINGS.get("max_tool_rounds", 6)) + 1):
                payload = {"model": MODEL, "messages": list(self.messages), "tools": backend.TOOLS,
                           "tool_choice": "auto", "parallel_tool_calls": False,
                           "max_tokens": int(backend.SETTINGS.get("max_response_tokens", 1600)),
                           "temperature": 0.8}
                body, headers = backend.api("/chat/completions", self.key, payload)
                served = body.get("model")
                if served and served not in (MODEL, MODEL.removesuffix(":free")):
                    raise RuntimeError("Strict policy blocked the response: returned model ID differs from the exact Hermes 3 405B free allowlist entry.")
                route = next((v for k, v in headers.items() if k.lower() == "x-routed-via"), "")
                if MC["models"][0].get("provider_id") == "septor" and route and "septor" not in route.lower():
                    raise RuntimeError("Strict route policy blocked the response: provider header does not match the allowlisted provider.")
                usage = body.get("usage", {}) if isinstance(body, dict) else {}
                reported_cost = usage.get("cost") if isinstance(usage, dict) else None
                if reported_cost is not None:
                    try:
                        if float(reported_cost) > 0:
                            raise RuntimeError("Response rejected: API reported nonzero inference cost. This lab is configured for $0 only.")
                    except (TypeError, ValueError):
                        pass
                choices = body.get("choices") or []
                if not choices:
                    raise RuntimeError("Model endpoint returned no choices.")
                message = choices[0].get("message", {})
                calls = message.get("tool_calls") or []
                if not calls:
                    content = message.get("content", "")
                    if isinstance(content, list):
                        content = "\n".join(str(x.get("text", "")) for x in content if isinstance(x, dict))
                    content = str(content or "")
                    self.messages.append({"role": "assistant", "content": content})
                    self.uiq.put(("answer", content, route))
                    return
                if round_no >= int(backend.SETTINGS.get("max_tool_rounds", 6)):
                    raise RuntimeError("Tool-round limit reached; stopped before further operations.")
                self.messages.append({"role": "assistant", "content": message.get("content"), "tool_calls": calls})
                for call in calls:
                    call_id = call.get("id", "")
                    fn = call.get("function", {})
                    name = fn.get("name", "")
                    try:
                        args = json.loads(fn.get("arguments") or "{}")
                        if name == "workspace_write":
                            result = {"ok": True, "result": self.do_workspace_write(args)}
                        elif name == "cli_run":
                            result = {"ok": True, "result": self.do_cli(args)}
                        else:
                            if name not in backend.FUNCS:
                                raise ValueError("Tool is not on the local allowlist.")
                            result = {"ok": True, "result": backend.FUNCS[name](args)}
                        self.uiq.put(("feed", "Tool " + name + ": " + ("ok" if result["ok"] else "blocked/error"), False))
                    except Exception as exc:
                        result = {"ok": False, "error": type(exc).__name__ + ": " + str(exc)[:450]}
                        self.uiq.put(("feed", "Tool " + name + " blocked/error: " + str(exc)[:350], True))
                    self.messages.append({"role": "tool", "tool_call_id": call_id,
                                          "content": json.dumps(result, ensure_ascii=False)[:12000]})
            raise RuntimeError("Maximum tool rounds reached.")
        except Exception as exc:
            self.uiq.put(("chat_error", str(exc)))
        finally:
            self.uiq.put(("chat_done",))

    def refresh_workspace(self):
        try:
            result = backend.t_list({"path": "."})
            self.file_list.delete(0, "end")
            for entry in result.get("entries", []):
                prefix = "[DIR] " if entry["type"] == "directory" else "[FILE] "
                self.file_list.insert("end", prefix + entry["name"])
            if not result.get("entries"):
                self.file_list.insert("end", "(empty workspace)")
            self.set_status("Workspace refreshed / " + str(len(result.get("entries", []))) + " entries")
            self.feed("Listed workspace entries: " + str(len(result.get("entries", []))))
        except Exception as exc:
            self.set_status("Workspace error: " + str(exc))

    def load_selected_file(self, _event=None):
        selection = self.file_list.curselection()
        if not selection:
            return
        label = self.file_list.get(selection[0])
        if label.startswith("[DIR] ") or label.startswith("("):
            return
        rel = label.removeprefix("[FILE] ").strip()
        try:
            result = backend.t_read({"path": rel})
            self.current_file.set(rel)
            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", result["content"])
            self.set_status("Loaded workspace file: " + rel)
        except Exception as exc:
            messagebox.showerror("Could not open workspace file", str(exc), parent=self.root)

    def save_editor(self):
        rel = self.current_file.get().strip()
        if not rel:
            messagebox.showwarning("Path required", "Enter a relative file path inside workspace/.", parent=self.root)
            return
        content = self.editor.get("1.0", "end-1c")
        try:
            p = backend.safe_path(rel, missing=True)
            if p.exists() and not p.is_file():
                raise ValueError("The target is not a regular file.")
            detail = "Save this file inside the isolated workspace?\n\nPath: " + str(p.relative_to(WORKSPACE))
            if p.exists():
                detail += "\n\nThis replaces the existing file."
            if not messagebox.askyesno("Approve workspace file write", detail, parent=self.root):
                self.set_status("File write declined; no changes made.")
                return
            if len(content.encode("utf-8")) > 200000:
                raise ValueError("File size exceeds 200 KB.")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            self.feed("Saved workspace file with approval: " + str(p.relative_to(WORKSPACE)))
            self.refresh_workspace()
            self.set_status("Saved: " + str(p.relative_to(WORKSPACE)))
        except Exception as exc:
            messagebox.showerror("Save blocked", str(exc), parent=self.root)

    def new_workspace_file(self):
        self.current_file.set("new_file.py")
        self.editor.delete("1.0", "end")
        self.set_status("New workspace draft. It is not saved until you approve Save.")

    def open_workspace(self):
        try:
            subprocess.Popen(["xdg-open", str(WORKSPACE)], close_fds=True)
        except Exception as exc:
            messagebox.showerror("Open workspace folder failed", str(exc), parent=self.root)

    def run_cli(self, op):
        if self.busy:
            return
        rel = self.cli_path.get().strip()
        args = {"operation": op, "cwd": "."}
        if rel:
            args["path"] = rel
        self.busy = True
        threading.Thread(target=self.cli_worker, args=(args,), daemon=True).start()
        self.set_status("Preparing guarded CLI operation…")

    def cli_worker(self, args):
        try:
            if args["operation"] == "list":
                res = backend.t_list({"path": args.get("path") or "."})
            else:
                res = self.do_cli(args)
            self.uiq.put(("feed", json.dumps(res, ensure_ascii=False)[:8000], False))
        except Exception as exc:
            self.uiq.put(("feed", str(exc), True))
        finally:
            self.uiq.put(("cli_done",))

    def listen(self):
        if self.busy:
            return
        if not self.key:
            self.set_status("Client key missing; voice input is available after key setup.")
        self.listen_button.configure(state="disabled")
        self.set_status("LISTENING ON THE G8 SYSTEM MIC FOR 8 SECONDS…")
        threading.Thread(target=self.listen_worker, daemon=True).start()

    def listen_worker(self):
        tempdir = Path(tempfile.mkdtemp(prefix="wah-lah-voice-"))
        raw = tempdir / "capture.pcm"
        wav_path = tempdir / "capture.wav"
        try:
            if not shutil.which("parecord"):
                raise RuntimeError("parecord is not available on this desktop.")
            if not VOICE_MODEL.is_dir():
                raise RuntimeError("Local Vosk model missing at " + str(VOICE_MODEL))
            cmd = ["timeout", "--signal=TERM", "8s", "parecord", "--device=" + MIC_SOURCE,
                   "--raw", "--format=s16le", "--rate=16000", "--channels=1", str(raw)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=11, check=False)
            if not raw.is_file() or raw.stat().st_size < 12000:
                detail = result.stderr.strip()[-250:]
                raise RuntimeError("G8 audio source did not produce enough audio." + ((" " + detail) if detail else ""))
            with wave.open(str(wav_path), "wb") as out:
                out.setnchannels(1)
                out.setsampwidth(2)
                out.setframerate(16000)
                out.writeframes(raw.read_bytes())
            with self.voice_model_lock:
                if self.voice_model is None:
                    from vosk import Model
                    self.voice_model = Model(str(VOICE_MODEL))
                model = self.voice_model
            from vosk import KaldiRecognizer
            recognizer = KaldiRecognizer(model, 16000)
            with wave.open(str(wav_path), "rb") as wavfile:
                while True:
                    frames = wavfile.readframes(4000)
                    if not frames:
                        break
                    recognizer.AcceptWaveform(frames)
                parsed = json.loads(recognizer.FinalResult())
            recognized = parsed.get("text", "").strip()
            if not recognized:
                raise RuntimeError("No clear speech was recognized. Try again closer to the G8 microphone.")
            self.uiq.put(("transcript", recognized))
        except Exception as exc:
            self.uiq.put(("listen_error", str(exc)))
        finally:
            shutil.rmtree(tempdir, ignore_errors=True)
            self.uiq.put(("listen_done",))

    def speak_last(self):
        if not self.last_response:
            self.set_status("No model answer to speak yet.")
            return
        text = self.last_response
        threading.Thread(target=self.speak_worker, args=(text,), daemon=True).start()

    def speak_worker(self, text):
        speaker = shutil.which("spd-say")
        if not speaker:
            self.uiq.put(("feed", "spd-say not installed; speech output unavailable.", True))
            return
        try:
            subprocess.run([speaker, "--wait", text[:3500]], timeout=45,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            self.uiq.put(("status", "Speech output finished."))
        except Exception as exc:
            self.uiq.put(("feed", "Speech output failed: " + str(exc), True))

    def poll_queue(self):
        try:
            while True:
                item = self.uiq.get_nowait()
                kind = item[0]
                if kind == "status":
                    self.set_status(item[1])
                elif kind == "feed":
                    self.feed(item[1], item[2])
                    self.set_status("Tool event recorded in this session.")
                elif kind == "model_check_done":
                    self.send_button.configure(state="normal" if item[1] and not self.busy else "disabled")
                elif kind == "approval":
                    _, title, details, event, result = item
                    result["approved"] = messagebox.askyesno(title, details, parent=self.root)
                    event.set()
                elif kind == "answer":
                    _, answer, route = item
                    self.last_response = answer
                    self.append_transcript("assistant", answer or "(empty model response)")
                    if route:
                        self.append_transcript("meta", "Provider route: " + str(route))
                    self.set_status("RESPONSE COMPLETE / fixed model / no fallback")
                    if self.voice_on.get() and answer:
                        threading.Thread(target=self.speak_worker, args=(answer,), daemon=True).start()
                elif kind == "chat_error":
                    self.append_transcript("error", item[1] + "\nNo alternate model or paid route was selected.")
                    self.set_status("CHAT ERROR / no fallback selected")
                elif kind == "chat_done":
                    self.busy = False
                    self.send_button.configure(state="normal" if self.last_model_check else "disabled")
                elif kind == "cli_done":
                    self.busy = False
                    self.set_status("Guarded CLI operation complete.")
                elif kind == "transcript":
                    self.input.insert("end", item[1])
                    self.input.see("end")
                    self.set_status("Speech converted to text. Review it, then press Send.")
                    self.input.focus_set()
                elif kind == "listen_error":
                    self.set_status("Voice input failed.")
                    messagebox.showerror("G8 voice input", item[1], parent=self.root)
                elif kind == "listen_done":
                    self.listen_button.configure(state="normal")
        except queue.Empty:
            pass
        self.root.after(100, self.poll_queue)

def main():
    root = tk.Tk()
    GalaxyApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

"""
Main application window – orchestrates all panels and core modules.

Layout:
  ┌──────────┬────────────────────────────────────┐
  │          │  Tabs: [Editor] [History]           │
  │  Bind    │                                    │
  │  List    │  (ScriptEditor or HistoryPanel)     │
  │  Panel   │                                    │
  │          │                                    │
  ├──────────┴────────────────────────────────────┤
  │        Control Panel (bottom bar)              │
  └────────────────────────────────────────────────┘
"""

from __future__ import annotations

import os
from tkinter import filedialog, messagebox, simpledialog
from typing import Optional

import customtkinter as ctk

from core.hotkey_manager import HotkeyManager
from core.models import Action, ExecutionRecord, Script
from core.player import Player
from core.recorder import Recorder
from core.script_manager import ScriptManager
from ui import theme as T
from ui.bind_list_panel import BindListPanel
from utils import constants as C
from ui.control_panel import ControlPanel
from ui.history_panel import HistoryPanel
from ui.script_editor import ScriptEditor
from ui.settings_dialog import SettingsDialog
from utils.logger import get_logger

logger = get_logger("ui.app")


class App(ctk.CTk):
    """BindClicker main application window."""

    def __init__(self) -> None:
        super().__init__()

        # -- Window --
        self.title("BindClicker")
        self.geometry("1060x640")
        self.minsize(900, 500)
        self.configure(fg_color=T.BG_DARK)
        
        if os.path.exists(C.APP_ICON):
            self.iconbitmap(C.APP_ICON)
            
        ctk.set_appearance_mode("dark")

        # -- Core modules --
        self.script_manager = ScriptManager()
        self.recorder = Recorder(on_action_recorded=self._on_action_recorded)
        self.player = Player(
            on_progress=self._on_playback_progress,
            on_finished=self._on_playback_finished,
        )
        self.hotkey_manager = HotkeyManager()

        self._current_script: Optional[Script] = None

        # -- Layout --
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # -- Sidebar (bind list) --
        self.bind_list = BindListPanel(
            self,
            on_select=self._on_bind_selected,
            on_new=self._on_new_bind,
            on_delete=self._on_delete_bind,
            on_import=self._on_import,
            on_export=self._on_export,
            on_rename=self._on_rename_bind,
        )
        self.bind_list.grid(row=0, column=0, sticky="nsew")

        # -- Main content area --
        content = ctk.CTkFrame(self, fg_color=T.BG_DARK)
        content.grid(row=0, column=1, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(1, weight=1)

        # Tab bar
        tab_bar = ctk.CTkFrame(content, fg_color=T.BG_PANEL, height=38, corner_radius=0)
        tab_bar.grid(row=0, column=0, sticky="ew")
        tab_bar.grid_propagate(False)

        self._tab_editor_btn = ctk.CTkButton(
            tab_bar, text="📝 Editor", width=100, height=32,
            font=(T.FONT_FAMILY, T.FONT_SIZE_SM, "bold"),
            fg_color=T.ACCENT_PRIMARY, hover_color=T.BTN_DEFAULT_HOVER,
            corner_radius=T.CORNER_RADIUS_SM,
            command=lambda: self._switch_tab("editor"),
        )
        self._tab_editor_btn.pack(side="left", padx=(T.PADDING, 4), pady=3)

        self._tab_history_btn = ctk.CTkButton(
            tab_bar, text="📊 History", width=100, height=32,
            font=(T.FONT_FAMILY, T.FONT_SIZE_SM, "bold"),
            fg_color=T.BG_CARD, hover_color=T.BG_HOVER,
            corner_radius=T.CORNER_RADIUS_SM,
            command=lambda: self._switch_tab("history"),
        )
        self._tab_history_btn.pack(side="left", padx=(0, 4), pady=3)

        # Content pages
        self._content_frame = ctk.CTkFrame(content, fg_color=T.BG_DARK)
        self._content_frame.grid(row=1, column=0, sticky="nsew")
        self._content_frame.columnconfigure(0, weight=1)
        self._content_frame.rowconfigure(0, weight=1)

        self.script_editor = ScriptEditor(
            self._content_frame,
            on_script_modified=self._on_script_modified,
        )

        self.history_panel = HistoryPanel(self._content_frame)

        self._current_tab = "editor"
        self.script_editor.grid(row=0, column=0, sticky="nsew")

        # -- Control panel (bottom) --
        self.control_panel = ControlPanel(
            self,
            on_record_toggle=self._toggle_recording,
            on_execute=self._execute_bind,
            on_stop=self._emergency_stop,
            on_speed_change=self._on_speed_change,
            on_repeat_change=self._on_repeat_change,
            on_delay_change=self._on_delay_change,
            on_settings=self._open_settings,
        )
        self.control_panel.grid(row=1, column=0, columnspan=2, sticky="ew")

        # -- Hotkeys --
        self._setup_hotkeys()

        # -- Initial data load --
        self._refresh_bind_list()

        # -- Cleanup on close --
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        logger.info("Application window initialised")

    # ===================================================================
    # Tab switching
    # ===================================================================

    def _switch_tab(self, tab: str) -> None:
        if tab == self._current_tab:
            return

        self._current_tab = tab

        if tab == "editor":
            self.history_panel.grid_forget()
            self.script_editor.grid(row=0, column=0, sticky="nsew")
            self._tab_editor_btn.configure(fg_color=T.ACCENT_PRIMARY)
            self._tab_history_btn.configure(fg_color=T.BG_CARD)
        else:
            self.script_editor.grid_forget()
            self.history_panel.grid(row=0, column=0, sticky="nsew")
            self._tab_editor_btn.configure(fg_color=T.BG_CARD)
            self._tab_history_btn.configure(fg_color=T.ACCENT_PRIMARY)

            # Refresh history when switching to the tab
            if self._current_script:
                history = self.script_manager.load_history(self._current_script.name)
                self.history_panel.load_history(history)

    # ===================================================================
    # Hotkeys
    # ===================================================================

    def _setup_hotkeys(self) -> None:
        hk = self.hotkey_manager
        hk.set_callback(HotkeyManager.ACTION_TOGGLE_RECORD, self._toggle_recording)
        hk.set_callback(HotkeyManager.ACTION_EXECUTE, self._execute_bind)
        hk.set_callback(HotkeyManager.ACTION_EMERGENCY_STOP, self._emergency_stop)
        hk.start()

        # Update button labels with current hotkey names
        self._update_hotkey_labels()

        # Tell the recorder which keys to ignore
        self.recorder.set_ignored_keys(hk.get_all_hotkey_keys())

    def _update_hotkey_labels(self) -> None:
        hk = self.hotkey_manager
        self.control_panel.update_hotkey_labels(
            hk.get_binding(HotkeyManager.ACTION_TOGGLE_RECORD),
            hk.get_binding(HotkeyManager.ACTION_EXECUTE),
            hk.get_binding(HotkeyManager.ACTION_EMERGENCY_STOP),
        )

    # ===================================================================
    # Bind list operations
    # ===================================================================

    def _refresh_bind_list(self) -> None:
        """Reload the sidebar with all saved scripts."""
        names = self.script_manager.list_scripts()
        items = []
        for name in names:
            script = self.script_manager.load_script(name)
            count = script.action_count if script else 0
            items.append((name, count))
        self.bind_list.refresh(items)

    def _on_bind_selected(self, name: str) -> None:
        """Load the selected bind into the editor."""
        script = self.script_manager.load_script(name)
        if script:
            self._current_script = script
            self.script_editor.load_script(script)
            if self._current_tab == "history":
                history = self.script_manager.load_history(name)
                self.history_panel.load_history(history)
            logger.info("Bind selected: '%s'", name)

    def _on_new_bind(self) -> None:
        """Create a new empty bind."""
        name = simpledialog.askstring(
            "New Bind", "Enter a name for the new bind:",
            parent=self,
        )
        if not name or not name.strip():
            return

        name = name.strip()
        if self.script_manager.script_exists(name):
            messagebox.showwarning("Name Exists", f"A bind named '{name}' already exists.")
            return

        script = Script(name=name)
        self.script_manager.save_script(script)
        self._refresh_bind_list()
        self.bind_list.select(name)
        logger.info("New bind created: '%s'", name)

    def _on_delete_bind(self, name: str) -> None:
        """Delete the selected bind."""
        if not messagebox.askyesno("Delete Bind", f"Delete '{name}'?\nThis cannot be undone."):
            return

        self.script_manager.delete_script(name)
        self._current_script = None
        self.script_editor.load_script(None)
        self._refresh_bind_list()
        logger.info("Bind deleted: '%s'", name)

    def _on_rename_bind(self, old_name: str) -> None:
        """Rename the selected bind."""
        new_name = simpledialog.askstring(
            "Rename Bind", f"New name for '{old_name}':",
            parent=self, initialvalue=old_name,
        )
        if not new_name or not new_name.strip() or new_name.strip() == old_name:
            return

        new_name = new_name.strip()
        if self.script_manager.script_exists(new_name):
            messagebox.showwarning("Name Exists", f"A bind named '{new_name}' already exists.")
            return

        self.script_manager.rename_script(old_name, new_name)
        self._refresh_bind_list()
        self.bind_list.select(new_name)
        self._on_bind_selected(new_name)
        logger.info("Bind renamed: '%s' → '%s'", old_name, new_name)

    def _on_import(self) -> None:
        """Import a script from a JSON file."""
        filepath = filedialog.askopenfilename(
            title="Import Bind",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            parent=self,
        )
        if not filepath:
            return

        script = self.script_manager.import_script(filepath)
        if script:
            self._refresh_bind_list()
            self.bind_list.select(script.name)
            self._on_bind_selected(script.name)
            logger.info("Bind imported: '%s'", script.name)
        else:
            messagebox.showerror("Import Failed", "Could not import the selected file.\nMake sure it is a valid BindClicker JSON.")

    def _on_export(self, name: str) -> None:
        """Export a script to a JSON file."""
        filepath = filedialog.asksaveasfilename(
            title="Export Bind",
            defaultextension=".json",
            initialfile=f"{name}.json",
            filetypes=[("JSON files", "*.json")],
            parent=self,
        )
        if not filepath:
            return

        if self.script_manager.export_script(name, filepath):
            logger.info("Bind exported: '%s' → %s", name, filepath)
        else:
            messagebox.showerror("Export Failed", "Could not export the bind.")

    # ===================================================================
    # Recording
    # ===================================================================

    def _toggle_recording(self) -> None:
        if self.player.is_running:
            return  # Don't record while executing

        if self.recorder.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self) -> None:
        """Show a 3-2-1 countdown then begin recording."""
        if self.player.is_running:
            return
        # Update ignored keys before recording
        self.recorder.set_ignored_keys(self.hotkey_manager.get_all_hotkey_keys())
        self._show_countdown(on_done=self._begin_recording_after_countdown)

    def _begin_recording_after_countdown(self) -> None:
        """Actually start the recorder after the countdown finishes."""
        # Set editor to live recording mode
        script_name = self._current_script.name if self._current_script else ""
        self.script_editor.set_recording_mode(True, script_name)
        self._switch_tab("editor")  # ensure editor tab is visible
        self.recorder.start()
        self.control_panel.set_status("recording")
        logger.info("Recording started via UI/hotkey")

    def _show_countdown(self, on_done) -> None:
        """Display a fullscreen 3-2-1 countdown overlay."""
        overlay = ctk.CTkFrame(self, fg_color="#000000")
        overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        overlay.lift()

        lbl_number = ctk.CTkLabel(
            overlay, text="3",
            font=(T.FONT_FAMILY, 120, "bold"),
            text_color=T.ACCENT_PRIMARY,
        )
        lbl_number.place(relx=0.5, rely=0.4, anchor="center")

        lbl_hint = ctk.CTkLabel(
            overlay, text="Get ready to record…",
            font=(T.FONT_FAMILY, T.FONT_SIZE_LG),
            text_color=T.TEXT_MUTED,
        )
        lbl_hint.place(relx=0.5, rely=0.58, anchor="center")

        # Color progression: purple → blue → green → GO
        steps = [
            ("3", T.ACCENT_PRIMARY),
            ("2", T.ACCENT_SECONDARY),
            ("1", T.STATUS_RECORDING),
        ]

        def tick(index=0):
            if index < len(steps):
                text, color = steps[index]
                lbl_number.configure(text=text, text_color=color)
                self.after(1000, lambda: tick(index + 1))
            else:
                # Show "GO!" briefly then remove overlay
                lbl_number.configure(text="GO!", text_color=T.BTN_EXECUTE)
                lbl_hint.configure(text="Recording…")
                self.after(400, lambda: self._finish_countdown(overlay, on_done))

        tick(0)

    def _finish_countdown(self, overlay, on_done) -> None:
        """Remove countdown overlay and call the callback."""
        overlay.destroy()
        if on_done:
            on_done()

    def _stop_recording(self) -> None:
        actions = self.recorder.stop()
        self.after(0, lambda: self.control_panel.set_status("idle"))
        self.after(0, lambda: self.control_panel.set_progress(""))
        self.script_editor.set_recording_mode(False)

        if not actions:
            logger.info("Recording stopped – no actions captured")
            return

        # If a bind is selected, ask if user wants to overwrite or create new
        if self._current_script:
            overwrite = messagebox.askyesno(
                "Save Recording",
                f"Save {len(actions)} actions to '{self._current_script.name}'?\n\n"
                "Yes → Replace current actions\n"
                "No → Create a new bind",
            )
            if overwrite:
                self._current_script.actions = actions
                self.script_manager.save_script(self._current_script)
                self.script_editor.load_script(self._current_script)
                self._refresh_bind_list()
                logger.info("Recording saved to existing bind: '%s'", self._current_script.name)
                return

        # Create new bind
        name = simpledialog.askstring(
            "Save Recording",
            f"Enter a name for the new bind ({len(actions)} actions):",
            parent=self,
        )
        if not name or not name.strip():
            return

        name = name.strip()
        script = Script(name=name, actions=actions)
        self.script_manager.save_script(script)
        self._current_script = script
        self._refresh_bind_list()
        self.bind_list.select(name)
        self.script_editor.load_script(script)
        logger.info("Recording saved as new bind: '%s' (%d actions)", name, len(actions))

    def _on_action_recorded(self, action: Action) -> None:
        """Callback from Recorder for each captured action (real-time)."""
        count = self.recorder.action_count
        # Update progress counter
        self.after(0, lambda: self.control_panel.set_progress(f"{count} actions recorded"))
        # Instantly append the new action row to the editor table
        self.after(0, lambda a=action: self.script_editor.append_action_live(a))

    # ===================================================================
    # Execution
    # ===================================================================

    def _execute_bind(self) -> None:
        if self.recorder.is_recording or self.player.is_running:
            return

        if not self._current_script or not self._current_script.actions:
            self.after(0, lambda: messagebox.showinfo(
                "No Bind", "Select a bind with actions to execute."))
            return

        # Apply current UI settings to the script
        self._current_script.speed_multiplier = self.control_panel.get_speed()
        self._current_script.repeat_count = self.control_panel.get_repeats()
        self._current_script.random_delay_ms = self.control_panel.get_random_delay()

        self.after(0, lambda: self.control_panel.set_status("executing"))
        self.player.start(self._current_script)
        logger.info(
            "Executing bind: '%s' (speed=%.2fx, repeats=%s, jitter=±%dms)",
            self._current_script.name,
            self._current_script.speed_multiplier,
            self._current_script.repeat_count or "∞",
            self._current_script.random_delay_ms,
        )

    def _on_playback_progress(
        self, rep: int, total_rep: int, act: int, total_act: int
    ) -> None:
        rep_str = f"{rep}/{total_rep}" if total_rep > 0 else f"{rep}/∞"
        text = f"Repeat {rep_str}  ·  Action {act}/{total_act}"
        self.after(0, lambda: self.control_panel.set_progress(text))

    def _on_playback_finished(self, record: ExecutionRecord) -> None:
        self.script_manager.add_execution_record(record)
        self.after(0, lambda: self.control_panel.set_status("idle"))
        self.after(0, lambda: self.control_panel.set_progress(""))

        # Refresh history if visible
        if self._current_tab == "history" and self._current_script:
            self.after(0, lambda: self.history_panel.load_history(
                self.script_manager.load_history(self._current_script.name)
            ))

        logger.info("Playback finished: %s", record.status)

    # ===================================================================
    # Emergency stop
    # ===================================================================

    def _emergency_stop(self) -> None:
        """Stop everything immediately."""
        if self.recorder.is_recording:
            self.recorder.stop()
            self.recorder.clear()
        if self.player.is_running:
            self.player.stop()
        self.after(0, lambda: self.control_panel.set_status("idle"))
        self.after(0, lambda: self.control_panel.set_progress(""))
        logger.info("Emergency stop triggered")

    # ===================================================================
    # Script modification from editor
    # ===================================================================

    def _on_script_modified(self, script: Script) -> None:
        """Called when the editor modifies the current script."""
        self.script_manager.save_script(script)
        self._refresh_bind_list()

    # ===================================================================
    # Settings
    # ===================================================================

    def _on_speed_change(self, value: float) -> None:
        if self._current_script:
            self._current_script.speed_multiplier = value

    def _on_repeat_change(self, value: int) -> None:
        if self._current_script:
            self._current_script.repeat_count = value

    def _on_delay_change(self, value: int) -> None:
        if self._current_script:
            self._current_script.random_delay_ms = value

    def _open_settings(self) -> None:
        """Open the hotkey settings dialog."""
        SettingsDialog(
            self,
            hotkey_manager=self.hotkey_manager,
            on_close=self._on_settings_closed,
        )

    def _on_settings_closed(self) -> None:
        """Refresh hotkey labels after settings changed."""
        self._update_hotkey_labels()
        self.recorder.set_ignored_keys(self.hotkey_manager.get_all_hotkey_keys())
        logger.info("Hotkey settings updated")

    # ===================================================================
    # Cleanup
    # ===================================================================

    def _on_close(self) -> None:
        """Clean shutdown."""
        if self.recorder.is_recording:
            self.recorder.stop()
        if self.player.is_running:
            self.player.stop()
        self.hotkey_manager.stop()
        logger.info("Application closing")
        self.destroy()

"""
Script editor – tabular view of all actions in a script.

Allows inline editing, reordering, adding and removing actions.
Uses a tkinter Treeview wrapped with customtkinter styling.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

import customtkinter as ctk

from core.models import Action, Script
from ui import theme as T


class ScriptEditor(ctk.CTkFrame):
    """Table view for editing script actions."""

    COLUMNS = ("idx", "type", "target", "position", "delay_before", "delay_after", "pressed")
    HEADERS = ("#", "Type", "Button/Key", "Position", "Delay Before (ms)", "Delay After (ms)", "State")
    WIDTHS = (40, 100, 90, 90, 110, 110, 60)

    def __init__(
        self,
        master,
        on_script_modified: Optional[Callable[[Script], None]] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color=T.BG_DARK, **kwargs)

        self._script: Optional[Script] = None
        self._on_script_modified = on_script_modified

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # -- Header --
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=T.PADDING, pady=(T.PADDING, T.PADDING_SM))
        header.columnconfigure(0, weight=1)

        self.lbl_title = ctk.CTkLabel(
            header, text="Script Editor",
            font=(T.FONT_FAMILY, T.FONT_SIZE_LG, "bold"),
            text_color=T.TEXT_PRIMARY,
        )
        self.lbl_title.grid(row=0, column=0, sticky="w")

        self.lbl_count = ctk.CTkLabel(
            header, text="",
            font=(T.FONT_FAMILY, T.FONT_SIZE_XS),
            text_color=T.TEXT_MUTED,
        )
        self.lbl_count.grid(row=0, column=1, sticky="e")

        # -- Treeview --
        tree_frame = ctk.CTkFrame(self, fg_color=T.BG_PANEL, corner_radius=T.CORNER_RADIUS)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=T.PADDING, pady=0)
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Script.Treeview",
            background=T.BG_PANEL,
            foreground=T.TEXT_PRIMARY,
            fieldbackground=T.BG_PANEL,
            borderwidth=0,
            font=(T.FONT_FAMILY, T.FONT_SIZE_SM),
            rowheight=28,
        )
        style.configure(
            "Script.Treeview.Heading",
            background=T.TABLE_HEADER,
            foreground=T.TEXT_SECONDARY,
            borderwidth=0,
            font=(T.FONT_FAMILY, T.FONT_SIZE_XS, "bold"),
        )
        style.map(
            "Script.Treeview",
            background=[("selected", T.TABLE_SELECTED)],
            foreground=[("selected", T.TEXT_PRIMARY)],
        )

        self.tree = ttk.Treeview(
            tree_frame,
            columns=self.COLUMNS,
            show="headings",
            style="Script.Treeview",
            selectmode="browse",
        )

        for col, hdr, w in zip(self.COLUMNS, self.HEADERS, self.WIDTHS):
            self.tree.heading(col, text=hdr)
            self.tree.column(col, width=w, minwidth=w, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        # Double-click to edit
        self.tree.bind("<Double-1>", self._on_double_click)

        # -- Button bar --
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=T.PADDING, pady=T.PADDING)

        self.btn_add = ctk.CTkButton(
            btn_frame, text="＋ Add Action", width=110, height=30,
            font=(T.FONT_FAMILY, T.FONT_SIZE_XS, "bold"),
            fg_color=T.ACCENT_PRIMARY, hover_color=T.BTN_DEFAULT_HOVER,
            corner_radius=T.CORNER_RADIUS_SM,
            command=self._add_action,
        )
        self.btn_add.pack(side="left", padx=(0, 6))

        self.btn_remove = ctk.CTkButton(
            btn_frame, text="✕ Remove", width=90, height=30,
            font=(T.FONT_FAMILY, T.FONT_SIZE_XS, "bold"),
            fg_color=T.BTN_DANGER, hover_color=T.BTN_DANGER_HOVER,
            corner_radius=T.CORNER_RADIUS_SM,
            command=self._remove_action,
        )
        self.btn_remove.pack(side="left", padx=(0, 6))

        self.btn_up = ctk.CTkButton(
            btn_frame, text="▲ Up", width=60, height=30,
            font=(T.FONT_FAMILY, T.FONT_SIZE_XS),
            fg_color=T.BG_CARD, hover_color=T.BG_HOVER,
            corner_radius=T.CORNER_RADIUS_SM,
            command=self._move_up,
        )
        self.btn_up.pack(side="left", padx=(0, 4))

        self.btn_down = ctk.CTkButton(
            btn_frame, text="▼ Down", width=70, height=30,
            font=(T.FONT_FAMILY, T.FONT_SIZE_XS),
            fg_color=T.BG_CARD, hover_color=T.BG_HOVER,
            corner_radius=T.CORNER_RADIUS_SM,
            command=self._move_down,
        )
        self.btn_down.pack(side="left")

        # Placeholder when no script selected
        self._placeholder = ctk.CTkLabel(
            self, text="Select or record a bind to edit",
            font=(T.FONT_FAMILY, T.FONT_SIZE_LG),
            text_color=T.TEXT_MUTED,
        )

    # -- Public API ----------------------------------------------------------

    @property
    def script(self) -> Optional[Script]:
        return self._script

    def load_script(self, script: Optional[Script]) -> None:
        """Display the actions of a script in the table."""
        self._script = script
        self._recording_mode = False
        self._refresh_tree()

    def set_recording_mode(self, active: bool, script_name: str = "") -> None:
        """Toggle live-recording visual mode."""
        self._recording_mode = active
        if active:
            self.tree.delete(*self.tree.get_children())
            self.lbl_title.configure(
                text=f"🔴 Recording: {script_name}" if script_name else "🔴 Recording…",
                text_color=T.STATUS_RECORDING,
            )
            self.lbl_count.configure(text="0 actions")
        else:
            self.lbl_title.configure(text_color=T.TEXT_PRIMARY)

    def append_action_live(self, action: "Action") -> None:
        """Append a single action row during live recording (no full refresh)."""
        idx = len(self.tree.get_children())
        tag = "even" if idx % 2 == 0 else "odd"
        self.tree.insert(
            "", "end",
            values=(
                idx + 1,
                action.display_type,
                action.display_target,
                action.display_position,
                f"{action.delay_before:.1f}",
                f"{action.delay_after:.1f}",
                "Press" if action.pressed else "Release",
            ),
            tags=(tag,),
        )
        self.tree.tag_configure("even", background=T.TABLE_ROW_EVEN)
        self.tree.tag_configure("odd", background=T.TABLE_ROW_ODD)
        self.lbl_count.configure(text=f"{idx + 1} actions")

        # Auto-scroll to the latest row
        children = self.tree.get_children()
        if children:
            self.tree.see(children[-1])

    def _refresh_tree(self) -> None:
        self.tree.delete(*self.tree.get_children())

        if self._script is None:
            self.lbl_title.configure(text="Script Editor")
            self.lbl_count.configure(text="")
            return

        self.lbl_title.configure(text=f"Script: {self._script.name}")
        self.lbl_count.configure(text=f"{self._script.action_count} actions")

        for i, action in enumerate(self._script.actions):
            tag = "even" if i % 2 == 0 else "odd"
            self.tree.insert(
                "", "end",
                values=(
                    i + 1,
                    action.display_type,
                    action.display_target,
                    action.display_position,
                    f"{action.delay_before:.1f}",
                    f"{action.delay_after:.1f}",
                    "Press" if action.pressed else "Release",
                ),
                tags=(tag,),
            )

        self.tree.tag_configure("even", background=T.TABLE_ROW_EVEN)
        self.tree.tag_configure("odd", background=T.TABLE_ROW_ODD)

    def _notify_modified(self) -> None:
        if self._script and self._on_script_modified:
            self._on_script_modified(self._script)

    # -- Editing actions -----------------------------------------------------

    def _selected_index(self) -> Optional[int]:
        sel = self.tree.selection()
        if not sel:
            return None
        item = self.tree.item(sel[0])
        return int(item["values"][0]) - 1  # 0-based

    def _add_action(self) -> None:
        if self._script is None:
            return
        new_action = Action(
            action_type="click", button="left",
            x=0, y=0, delay_before=100, delay_after=0, pressed=True,
        )
        self._script.actions.append(new_action)
        self._refresh_tree()
        self._notify_modified()

    def _remove_action(self) -> None:
        idx = self._selected_index()
        if idx is None or self._script is None:
            return
        if 0 <= idx < len(self._script.actions):
            self._script.actions.pop(idx)
            self._refresh_tree()
            self._notify_modified()

    def _move_up(self) -> None:
        idx = self._selected_index()
        if idx is None or self._script is None or idx <= 0:
            return
        actions = self._script.actions
        actions[idx], actions[idx - 1] = actions[idx - 1], actions[idx]
        self._refresh_tree()
        self._notify_modified()

    def _move_down(self) -> None:
        idx = self._selected_index()
        if idx is None or self._script is None:
            return
        actions = self._script.actions
        if idx >= len(actions) - 1:
            return
        actions[idx], actions[idx + 1] = actions[idx + 1], actions[idx]
        self._refresh_tree()
        self._notify_modified()

    # -- Inline edit (double-click) ------------------------------------------

    def _on_double_click(self, event) -> None:
        """Open a small entry widget over the clicked cell for inline editing."""
        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        column = self.tree.identify_column(event.x)
        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return

        col_idx = int(column.replace("#", "")) - 1
        col_name = self.COLUMNS[col_idx]

        # Only allow editing certain columns
        editable = ("target", "position", "delay_before", "delay_after")
        if col_name not in editable:
            return

        # Get cell bounding box
        bbox = self.tree.bbox(row_id, column)
        if not bbox:
            return

        item = self.tree.item(row_id)
        current_value = str(item["values"][col_idx])
        row_index = int(item["values"][0]) - 1

        # Create entry widget
        entry = tk.Entry(
            self.tree, font=(T.FONT_FAMILY, T.FONT_SIZE_SM),
            bg=T.BG_INPUT, fg=T.TEXT_PRIMARY,
            insertbackground=T.TEXT_PRIMARY,
            relief="flat", justify="center",
        )
        entry.insert(0, current_value)
        entry.select_range(0, "end")
        entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])
        entry.focus_set()

        def save_edit(_event=None):
            new_value = entry.get()
            entry.destroy()
            self._apply_edit(row_index, col_name, new_value)

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", save_edit)
        entry.bind("<Escape>", lambda _: entry.destroy())

    def _apply_edit(self, row_index: int, col_name: str, value: str) -> None:
        if self._script is None or row_index >= len(self._script.actions):
            return

        action = self._script.actions[row_index]

        try:
            if col_name == "target":
                action.button = value
            elif col_name == "position":
                # Parse "(x, y)" format
                clean = value.strip("() ").replace(",", " ")
                parts = clean.split()
                if len(parts) == 2:
                    action.x = int(parts[0])
                    action.y = int(parts[1])
            elif col_name == "delay_before":
                action.delay_before = float(value)
            elif col_name == "delay_after":
                action.delay_after = float(value)
        except (ValueError, IndexError):
            pass  # Ignore bad input

        self._refresh_tree()
        self._notify_modified()

"""
History panel – displays execution history for a selected bind.

Shows a table of past executions with date, duration, actions and status,
plus a summary counter at the top.
"""

from __future__ import annotations

from tkinter import ttk
from typing import Optional

import customtkinter as ctk

from core.models import ScriptHistory
from ui import theme as T


class HistoryPanel(ctk.CTkFrame):
    """Execution history view for a selected bind."""

    COLUMNS = ("date", "duration", "actions", "status")
    HEADERS = ("Date / Time", "Duration", "Actions", "Status")
    WIDTHS = (180, 100, 80, 100)

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=T.BG_DARK, **kwargs)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # -- Header with counter --
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=T.PADDING, pady=(T.PADDING, T.PADDING_SM))
        header.columnconfigure(0, weight=1)

        self.lbl_title = ctk.CTkLabel(
            header, text="Execution History",
            font=(T.FONT_FAMILY, T.FONT_SIZE_LG, "bold"),
            text_color=T.TEXT_PRIMARY,
        )
        self.lbl_title.grid(row=0, column=0, sticky="w")

        self.lbl_total = ctk.CTkLabel(
            header, text="",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SM, "bold"),
            text_color=T.TEXT_ACCENT,
        )
        self.lbl_total.grid(row=0, column=1, sticky="e")

        # -- Treeview --
        tree_frame = ctk.CTkFrame(self, fg_color=T.BG_PANEL, corner_radius=T.CORNER_RADIUS)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=T.PADDING, pady=(0, T.PADDING))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        style = ttk.Style()
        style.configure(
            "History.Treeview",
            background=T.BG_PANEL,
            foreground=T.TEXT_PRIMARY,
            fieldbackground=T.BG_PANEL,
            borderwidth=0,
            font=(T.FONT_FAMILY, T.FONT_SIZE_SM),
            rowheight=28,
        )
        style.configure(
            "History.Treeview.Heading",
            background=T.TABLE_HEADER,
            foreground=T.TEXT_SECONDARY,
            borderwidth=0,
            font=(T.FONT_FAMILY, T.FONT_SIZE_XS, "bold"),
        )
        style.map(
            "History.Treeview",
            background=[("selected", T.TABLE_SELECTED)],
            foreground=[("selected", T.TEXT_PRIMARY)],
        )

        self.tree = ttk.Treeview(
            tree_frame,
            columns=self.COLUMNS,
            show="headings",
            style="History.Treeview",
            selectmode="browse",
        )

        for col, hdr, w in zip(self.COLUMNS, self.HEADERS, self.WIDTHS):
            self.tree.heading(col, text=hdr)
            self.tree.column(col, width=w, minwidth=w, anchor="center")

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    # -- Public API ----------------------------------------------------------

    def load_history(self, history: Optional[ScriptHistory]) -> None:
        """Populate the table with history records."""
        self.tree.delete(*self.tree.get_children())

        if history is None or history.total_runs == 0:
            self.lbl_title.configure(text="Execution History")
            self.lbl_total.configure(text="No executions yet")
            return

        self.lbl_title.configure(text=f"History: {history.script_name}")
        self.lbl_total.configure(text=f"{history.total_runs} total runs")

        # Show most recent first
        for i, rec in enumerate(reversed(history.records)):
            tag = "even" if i % 2 == 0 else "odd"

            # Format date
            date_str = rec.started_at
            if "T" in date_str:
                date_str = date_str.replace("T", "  ")
                if "." in date_str:
                    date_str = date_str.split(".")[0]

            # Format duration
            if rec.duration_ms < 1000:
                dur_str = f"{rec.duration_ms:.0f} ms"
            else:
                dur_str = f"{rec.duration_ms / 1000:.1f} s"

            # Status with icon
            status_icons = {
                "completed": "✅ Completed",
                "stopped": "⏹ Stopped",
                "error": "❌ Error",
                "running": "▶ Running",
            }
            status_str = status_icons.get(rec.status, rec.status)

            self.tree.insert(
                "", "end",
                values=(date_str, dur_str, rec.actions_executed, status_str),
                tags=(tag,),
            )

        self.tree.tag_configure("even", background=T.TABLE_ROW_EVEN)
        self.tree.tag_configure("odd", background=T.TABLE_ROW_ODD)

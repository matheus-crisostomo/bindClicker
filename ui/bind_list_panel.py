"""
Sidebar panel listing all saved binds.

Features:
  - Scrollable list of bind cards
  - New / Delete / Import / Export buttons
  - Click to select a bind
"""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from ui import theme as T


class BindCard(ctk.CTkFrame):
    """A single clickable card representing a saved bind."""

    def __init__(
        self,
        master,
        name: str,
        action_count: int,
        on_click: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        super().__init__(
            master,
            fg_color=T.BG_CARD,
            corner_radius=T.CORNER_RADIUS_SM,
            cursor="hand2",
            **kwargs,
        )
        self._name = name
        self._on_click = on_click
        self._selected = False

        # Layout
        self.columnconfigure(0, weight=1)

        self.lbl_name = ctk.CTkLabel(
            self, text=name,
            font=(T.FONT_FAMILY, T.FONT_SIZE_MD, "bold"),
            text_color=T.TEXT_PRIMARY,
            anchor="w",
        )
        self.lbl_name.grid(row=0, column=0, sticky="w", padx=T.PADDING, pady=(T.PADDING_SM, 0))

        self.lbl_info = ctk.CTkLabel(
            self,
            text=f"{action_count} actions",
            font=(T.FONT_FAMILY, T.FONT_SIZE_XS),
            text_color=T.TEXT_MUTED,
            anchor="w",
        )
        self.lbl_info.grid(row=1, column=0, sticky="w", padx=T.PADDING, pady=(0, T.PADDING_SM))

        # Click events on the whole card
        for widget in (self, self.lbl_name, self.lbl_info):
            widget.bind("<Button-1>", self._handle_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

    @property
    def name(self) -> str:
        return self._name

    def set_selected(self, selected: bool) -> None:
        self._selected = selected
        self.configure(fg_color=T.TABLE_SELECTED if selected else T.BG_CARD)
        self.configure(border_width=2 if selected else 0)
        if selected:
            self.configure(border_color=T.ACCENT_PRIMARY)

    def _handle_click(self, _event=None) -> None:
        if self._on_click:
            self._on_click(self._name)

    def _on_enter(self, _event=None) -> None:
        if not self._selected:
            self.configure(fg_color=T.BG_HOVER)

    def _on_leave(self, _event=None) -> None:
        if not self._selected:
            self.configure(fg_color=T.BG_CARD)


class BindListPanel(ctk.CTkFrame):
    """Sidebar listing all saved binds with action buttons."""

    def __init__(
        self,
        master,
        on_select: Optional[Callable[[str], None]] = None,
        on_new: Optional[Callable] = None,
        on_delete: Optional[Callable[[str], None]] = None,
        on_import: Optional[Callable] = None,
        on_export: Optional[Callable[[str], None]] = None,
        on_rename: Optional[Callable[[str], None]] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color=T.BG_PANEL, width=T.SIDEBAR_WIDTH, **kwargs)

        self._on_select = on_select
        self._on_new = on_new
        self._on_delete = on_delete
        self._on_import = on_import
        self._on_export = on_export
        self._on_rename = on_rename
        self._cards: dict[str, BindCard] = {}
        self._selected: Optional[str] = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_propagate(False)

        # -- Header --
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=T.PADDING, pady=(T.PADDING, T.PADDING_SM))
        header.columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header, text="Binds",
            font=(T.FONT_FAMILY, T.FONT_SIZE_XL, "bold"),
            text_color=T.TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        # -- Scrollable list --
        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=T.BG_HOVER,
            scrollbar_button_hover_color=T.ACCENT_PRIMARY,
        )
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=T.PADDING_SM, pady=0)
        self._scroll.columnconfigure(0, weight=1)

        # -- Button bar --
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=T.PADDING, pady=T.PADDING)
        btn_frame.columnconfigure((0, 1), weight=1)

        self.btn_new = ctk.CTkButton(
            btn_frame, text="＋ New",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SM, "bold"),
            fg_color=T.ACCENT_PRIMARY,
            hover_color=T.BTN_DEFAULT_HOVER,
            corner_radius=T.CORNER_RADIUS_SM,
            height=32, command=self._handle_new,
        )
        self.btn_new.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_delete = ctk.CTkButton(
            btn_frame, text="✕ Delete",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SM, "bold"),
            fg_color=T.BTN_DANGER,
            hover_color=T.BTN_DANGER_HOVER,
            corner_radius=T.CORNER_RADIUS_SM,
            height=32, command=self._handle_delete,
        )
        self.btn_delete.grid(row=0, column=1, sticky="ew", padx=(4, 0))

        # Import / Export row
        io_frame = ctk.CTkFrame(self, fg_color="transparent")
        io_frame.grid(row=3, column=0, sticky="ew", padx=T.PADDING, pady=(0, T.PADDING))
        io_frame.columnconfigure((0, 1, 2), weight=1)

        self.btn_import = ctk.CTkButton(
            io_frame, text="📥 Import",
            font=(T.FONT_FAMILY, T.FONT_SIZE_XS),
            fg_color=T.BG_CARD,
            hover_color=T.BG_HOVER,
            corner_radius=T.CORNER_RADIUS_SM,
            height=28, command=self._handle_import,
        )
        self.btn_import.grid(row=0, column=0, sticky="ew", padx=(0, 3))

        self.btn_export = ctk.CTkButton(
            io_frame, text="📤 Export",
            font=(T.FONT_FAMILY, T.FONT_SIZE_XS),
            fg_color=T.BG_CARD,
            hover_color=T.BG_HOVER,
            corner_radius=T.CORNER_RADIUS_SM,
            height=28, command=self._handle_export,
        )
        self.btn_export.grid(row=0, column=1, sticky="ew", padx=3)

        self.btn_rename = ctk.CTkButton(
            io_frame, text="✏ Rename",
            font=(T.FONT_FAMILY, T.FONT_SIZE_XS),
            fg_color=T.BG_CARD,
            hover_color=T.BG_HOVER,
            corner_radius=T.CORNER_RADIUS_SM,
            height=28, command=self._handle_rename,
        )
        self.btn_rename.grid(row=0, column=2, sticky="ew", padx=(3, 0))

    # -- Public API ----------------------------------------------------------

    @property
    def selected(self) -> Optional[str]:
        return self._selected

    def refresh(self, scripts: list[tuple[str, int]]) -> None:
        """Rebuild the card list.

        Args:
            scripts: list of (name, action_count) tuples.
        """
        # Remove old cards
        for card in self._cards.values():
            card.destroy()
        self._cards.clear()

        for i, (name, count) in enumerate(scripts):
            card = BindCard(
                self._scroll, name=name, action_count=count,
                on_click=self._handle_select,
            )
            card.grid(row=i, column=0, sticky="ew", pady=(0, 4))
            self._cards[name] = card

        # Restore selection
        if self._selected and self._selected in self._cards:
            self._cards[self._selected].set_selected(True)
        elif self._selected and self._selected not in self._cards:
            self._selected = None

    def select(self, name: str) -> None:
        """Programmatically select a bind."""
        self._handle_select(name)

    # -- Handlers ------------------------------------------------------------

    def _handle_select(self, name: str) -> None:
        # Deselect previous
        if self._selected and self._selected in self._cards:
            self._cards[self._selected].set_selected(False)
        self._selected = name
        if name in self._cards:
            self._cards[name].set_selected(True)
        if self._on_select:
            self._on_select(name)

    def _handle_new(self) -> None:
        if self._on_new:
            self._on_new()

    def _handle_delete(self) -> None:
        if self._selected and self._on_delete:
            self._on_delete(self._selected)

    def _handle_import(self) -> None:
        if self._on_import:
            self._on_import()

    def _handle_export(self) -> None:
        if self._selected and self._on_export:
            self._on_export(self._selected)

    def _handle_rename(self) -> None:
        if self._selected and self._on_rename:
            self._on_rename(self._selected)

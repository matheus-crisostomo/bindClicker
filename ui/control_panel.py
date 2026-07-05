"""
Control panel – Record / Execute / Stop buttons, status indicator,
speed slider, repeat count, and random delay controls.
"""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from ui import theme as T


class ControlPanel(ctk.CTkFrame):
    """Bottom bar with playback controls and status indicator."""

    def __init__(
        self,
        master,
        on_record_toggle: Optional[Callable] = None,
        on_execute: Optional[Callable] = None,
        on_stop: Optional[Callable] = None,
        on_speed_change: Optional[Callable[[float], None]] = None,
        on_repeat_change: Optional[Callable[[int], None]] = None,
        on_delay_change: Optional[Callable[[int], None]] = None,
        on_settings: Optional[Callable] = None,
        **kwargs,
    ):
        super().__init__(master, fg_color=T.BG_PANEL, corner_radius=0, **kwargs)

        self._on_record_toggle = on_record_toggle
        self._on_execute = on_execute
        self._on_stop = on_stop
        self._on_speed_change = on_speed_change
        self._on_repeat_change = on_repeat_change
        self._on_delay_change = on_delay_change
        self._on_settings = on_settings

        self._status = "idle"

        self.columnconfigure(1, weight=1)

        # ===================================================================
        # LEFT: Action buttons
        # ===================================================================
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=0, column=0, padx=T.PADDING, pady=T.PADDING, sticky="w")

        self.btn_record = ctk.CTkButton(
            btn_frame, text="● Record (F6)", width=130, height=38,
            font=(T.FONT_FAMILY, T.FONT_SIZE_MD, "bold"),
            fg_color=T.BTN_RECORD, hover_color=T.BTN_RECORD_HOVER,
            corner_radius=T.CORNER_RADIUS,
            command=self._handle_record,
        )
        self.btn_record.grid(row=0, column=0, padx=(0, 8))

        self.btn_execute = ctk.CTkButton(
            btn_frame, text="▶ Execute (F7)", width=140, height=38,
            font=(T.FONT_FAMILY, T.FONT_SIZE_MD, "bold"),
            fg_color=T.BTN_EXECUTE, hover_color=T.BTN_EXECUTE_HOVER,
            corner_radius=T.CORNER_RADIUS,
            command=self._handle_execute,
        )
        self.btn_execute.grid(row=0, column=1, padx=(0, 8))

        self.btn_stop = ctk.CTkButton(
            btn_frame, text="■ Stop (F8)", width=120, height=38,
            font=(T.FONT_FAMILY, T.FONT_SIZE_MD, "bold"),
            fg_color=T.BTN_STOP, hover_color=T.BTN_STOP_HOVER,
            corner_radius=T.CORNER_RADIUS,
            command=self._handle_stop,
        )
        self.btn_stop.grid(row=0, column=2, padx=(0, 8))

        # ===================================================================
        # CENTER: Status indicator
        # ===================================================================
        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.grid(row=0, column=1, sticky="")

        self.lbl_status = ctk.CTkLabel(
            status_frame, text=T.STATUS_LABELS["idle"],
            font=(T.FONT_FAMILY, T.FONT_SIZE_LG, "bold"),
            text_color=T.STATUS_IDLE,
        )
        self.lbl_status.pack()

        self.lbl_progress = ctk.CTkLabel(
            status_frame, text="",
            font=(T.FONT_FAMILY, T.FONT_SIZE_XS),
            text_color=T.TEXT_MUTED,
        )
        self.lbl_progress.pack()

        # ===================================================================
        # RIGHT: Settings controls
        # ===================================================================
        ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctrl_frame.grid(row=0, column=2, padx=T.PADDING, pady=T.PADDING, sticky="e")

        # -- Speed --
        ctk.CTkLabel(
            ctrl_frame, text="Speed",
            font=(T.FONT_FAMILY, T.FONT_SIZE_XS),
            text_color=T.TEXT_MUTED,
        ).grid(row=0, column=0, sticky="w")

        self.lbl_speed_val = ctk.CTkLabel(
            ctrl_frame, text="1.0x",
            font=(T.FONT_FAMILY, T.FONT_SIZE_XS, "bold"),
            text_color=T.TEXT_ACCENT,
            width=40,
        )
        self.lbl_speed_val.grid(row=0, column=1, sticky="e")

        self.slider_speed = ctk.CTkSlider(
            ctrl_frame, from_=0.25, to=4.0, number_of_steps=15,
            width=120, height=16,
            button_color=T.ACCENT_PRIMARY,
            button_hover_color=T.ACCENT_SECONDARY,
            progress_color=T.ACCENT_PRIMARY,
            fg_color=T.BG_CARD,
            command=self._handle_speed,
        )
        self.slider_speed.set(1.0)
        self.slider_speed.grid(row=1, column=0, columnspan=2, pady=(2, 6))

        # -- Repeats --
        ctk.CTkLabel(
            ctrl_frame, text="Repeats",
            font=(T.FONT_FAMILY, T.FONT_SIZE_XS),
            text_color=T.TEXT_MUTED,
        ).grid(row=2, column=0, sticky="w")

        self.entry_repeats = ctk.CTkEntry(
            ctrl_frame, width=50, height=24,
            font=(T.FONT_FAMILY, T.FONT_SIZE_XS),
            fg_color=T.BG_INPUT, border_color=T.BORDER_DEFAULT,
            text_color=T.TEXT_PRIMARY,
            placeholder_text="1",
        )
        self.entry_repeats.insert(0, "1")
        self.entry_repeats.grid(row=2, column=1, sticky="e")
        self.entry_repeats.bind("<FocusOut>", self._handle_repeats)
        self.entry_repeats.bind("<Return>", self._handle_repeats)

        # -- Random Delay --
        ctk.CTkLabel(
            ctrl_frame, text="Jitter ±ms",
            font=(T.FONT_FAMILY, T.FONT_SIZE_XS),
            text_color=T.TEXT_MUTED,
        ).grid(row=3, column=0, sticky="w", pady=(4, 0))

        self.entry_delay = ctk.CTkEntry(
            ctrl_frame, width=50, height=24,
            font=(T.FONT_FAMILY, T.FONT_SIZE_XS),
            fg_color=T.BG_INPUT, border_color=T.BORDER_DEFAULT,
            text_color=T.TEXT_PRIMARY,
            placeholder_text="0",
        )
        self.entry_delay.insert(0, "0")
        self.entry_delay.grid(row=3, column=1, sticky="e", pady=(4, 0))
        self.entry_delay.bind("<FocusOut>", self._handle_delay)
        self.entry_delay.bind("<Return>", self._handle_delay)

        # -- Settings button --
        self.btn_settings = ctk.CTkButton(
            ctrl_frame, text="⚙ Hotkeys",
            font=(T.FONT_FAMILY, T.FONT_SIZE_XS),
            fg_color=T.BG_CARD, hover_color=T.BG_HOVER,
            corner_radius=T.CORNER_RADIUS_SM,
            width=80, height=24,
            command=self._handle_settings,
        )
        self.btn_settings.grid(row=4, column=0, columnspan=2, pady=(6, 0), sticky="ew")

    # -- Public API ----------------------------------------------------------

    def set_status(self, status: str) -> None:
        """Update the status indicator: 'idle', 'recording', 'executing', 'error'."""
        self._status = status
        label = T.STATUS_LABELS.get(status, f"● {status}")
        color = T.STATUS_COLORS.get(status, T.STATUS_IDLE)
        self.lbl_status.configure(text=label, text_color=color)

        # Update button states
        is_busy = status in ("recording", "executing")
        self.btn_record.configure(
            text="■ Stop Rec" if status == "recording" else "● Record (F6)",
        )
        self.btn_execute.configure(state="disabled" if status == "recording" else "normal")

    def set_progress(self, text: str) -> None:
        """Update the progress label (e.g. 'Repeat 2/5 – Action 3/12')."""
        self.lbl_progress.configure(text=text)

    def update_hotkey_labels(self, record_key: str, execute_key: str, stop_key: str) -> None:
        """Update button text with current hotkey names."""
        self.btn_record.configure(
            text=f"● Record ({record_key.upper()})"
            if self._status != "recording"
            else "■ Stop Rec",
        )
        self.btn_execute.configure(text=f"▶ Execute ({execute_key.upper()})")
        self.btn_stop.configure(text=f"■ Stop ({stop_key.upper()})")

    def get_speed(self) -> float:
        return round(self.slider_speed.get(), 2)

    def get_repeats(self) -> int:
        try:
            val = self.entry_repeats.get().strip()
            if val in ("", "0", "∞", "inf"):
                return 0
            return max(1, int(val))
        except ValueError:
            return 1

    def get_random_delay(self) -> int:
        try:
            return max(0, int(self.entry_delay.get().strip()))
        except ValueError:
            return 0

    # -- Handlers ------------------------------------------------------------

    def _handle_record(self) -> None:
        if self._on_record_toggle:
            self._on_record_toggle()

    def _handle_execute(self) -> None:
        if self._on_execute:
            self._on_execute()

    def _handle_stop(self) -> None:
        if self._on_stop:
            self._on_stop()

    def _handle_speed(self, value: float) -> None:
        rounded = round(value, 2)
        self.lbl_speed_val.configure(text=f"{rounded}x")
        if self._on_speed_change:
            self._on_speed_change(rounded)

    def _handle_repeats(self, _event=None) -> None:
        if self._on_repeat_change:
            self._on_repeat_change(self.get_repeats())

    def _handle_delay(self, _event=None) -> None:
        if self._on_delay_change:
            self._on_delay_change(self.get_random_delay())

    def _handle_settings(self) -> None:
        if self._on_settings:
            self._on_settings()

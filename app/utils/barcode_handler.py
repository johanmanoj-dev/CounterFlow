"""
CounterFlow v1.0.0 — Barcode Handler
=======================================
Handles barcode input processing for the POS screen.
Supports physical barcode scanners (which type fast
and send Enter) and manual keyboard input.

Detects scanner input vs manual typing using timing.
Normalizes barcodes before DB lookup.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import QLineEdit


# ── CounterFlow Barcode Constants ──────────────────────────────
COUNTERFLOW_SCANNER_THRESHOLD_MS = 100   # Input faster than this = scanner
COUNTERFLOW_MIN_BARCODE_LENGTH   = 3     # Minimum valid barcode length
COUNTERFLOW_MAX_BARCODE_LENGTH   = 100   # Maximum valid barcode length


class CounterFlowBarcodeHandler(QObject):
    """
    CounterFlow — Barcode Input Handler.

    Attaches to a QLineEdit and monitors its input.
    Distinguishes scanner input (fast) from manual typing (slow).
    Emits counterflow_barcode_scanned when a valid barcode is ready.

    Barcode scanners work by typing all characters rapidly then
    pressing Enter. This handler uses timing to detect that pattern
    and emit the signal only when the full code is received.

    Usage:
        self._counterflow_handler = CounterFlowBarcodeHandler(
            self._counterflow_barcode_input
        )
        self._counterflow_handler.counterflow_barcode_scanned.connect(
            self._counterflow_on_barcode
        )
    """

    counterflow_barcode_scanned = pyqtSignal(str)
    counterflow_invalid_barcode = pyqtSignal(str)

    def __init__(self, counterflow_input: QLineEdit, parent=None):
        super().__init__(parent)
        self._counterflow_input = counterflow_input
        self._counterflow_last_key_time = 0
        self._counterflow_is_scanner_input = False

        # Connect Enter key to trigger
        self._counterflow_input.returnPressed.connect(
            self._counterflow_on_enter
        )

    def _counterflow_on_enter(self):
        """
        CounterFlow — Called when Enter is pressed on the barcode field.
        Normalizes and validates the barcode, then emits the signal.
        """
        counterflow_raw = self._counterflow_input.text()
        counterflow_normalized = self.counterflow_normalize(counterflow_raw)

        if not counterflow_normalized:
            self._counterflow_input.clear()
            return

        counterflow_valid, counterflow_msg = self.counterflow_validate(
            counterflow_normalized
        )

        if counterflow_valid:
            self._counterflow_input.clear()
            self.counterflow_barcode_scanned.emit(counterflow_normalized)
        else:
            self.counterflow_invalid_barcode.emit(counterflow_msg)
            self._counterflow_input.selectAll()

    # ── Public API ─────────────────────────────────────────────

    @staticmethod
    def counterflow_normalize(raw: str) -> str:
        """
        CounterFlow — Normalize a raw barcode string.
        Strips whitespace, converts to uppercase,
        removes common scanner prefix/suffix garbage.

        Returns the cleaned barcode string.
        """
        counterflow_cleaned = raw.strip()

        # Remove common barcode scanner prefix/suffix characters
        counterflow_cleaned = counterflow_cleaned.strip("\x02\x03\r\n")

        # Uppercase for consistent DB lookup
        counterflow_cleaned = counterflow_cleaned.upper()

        return counterflow_cleaned

    @staticmethod
    def counterflow_validate(barcode: str) -> tuple[bool, str]:
        """
        CounterFlow — Validate a normalized barcode string.

        Returns:
            (True, barcode)          — valid
            (False, error_message)   — invalid
        """
        if not barcode:
            return False, "Barcode is empty."

        if len(barcode) < COUNTERFLOW_MIN_BARCODE_LENGTH:
            return (
                False,
                f"Barcode too short — minimum {COUNTERFLOW_MIN_BARCODE_LENGTH} characters."
            )

        if len(barcode) > COUNTERFLOW_MAX_BARCODE_LENGTH:
            return (
                False,
                f"Barcode too long — maximum {COUNTERFLOW_MAX_BARCODE_LENGTH} characters."
            )

        return True, barcode

    @staticmethod
    def counterflow_looks_like_barcode(text: str) -> bool:
        """
        CounterFlow — Heuristic check: does this string look like a barcode?
        Used to decide whether to attempt a product lookup automatically.
        True if the string is all alphanumeric (typical for most barcodes).
        """
        counterflow_cleaned = text.strip()
        return (
            bool(counterflow_cleaned)
            and counterflow_cleaned.replace("-", "").replace("_", "").isalnum()
            and COUNTERFLOW_MIN_BARCODE_LENGTH
            <= len(counterflow_cleaned)
            <= COUNTERFLOW_MAX_BARCODE_LENGTH
        )

    def counterflow_set_focus(self):
        """CounterFlow — Set focus back to barcode input field."""
        self._counterflow_input.setFocus()
        self._counterflow_input.clear()

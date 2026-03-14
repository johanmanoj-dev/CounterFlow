"""
CounterFlow v1.0.0 — PDF Invoice Generator
============================================
Generates a clean, professional PDF invoice
for any finalized CounterFlow transaction.

Uses ReportLab to produce a thermal-style invoice
that can be saved or printed directly.

Output: PDF saved to COUNTERFLOW_INVOICE_OUTPUT_DIR
        named as CF-00042.pdf
"""

import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import (
    HexColor, black, white, lightgrey
)
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle,
    Paragraph, Spacer, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

from app.db.models import CounterFlowInvoice
from app.config import (
    COUNTERFLOW_APP_NAME,
    COUNTERFLOW_VERSION,
    COUNTERFLOW_INVOICE_OUTPUT_DIR,
    COUNTERFLOW_CURRENCY_SYMBOL,
)
from app.utils.formatters import (
    counterflow_format_currency,
    counterflow_format_datetime,
    counterflow_format_mobile,
)


# ── CounterFlow PDF Color Palette ─────────────────────────────
CF_BLACK       = HexColor("#111827")
CF_GRAY        = HexColor("#6b7280")
CF_LIGHT_GRAY  = HexColor("#f3f4f6")
CF_BORDER      = HexColor("#e5e7eb")
CF_SUCCESS     = HexColor("#16a34a")
CF_WARNING     = HexColor("#d97706")
CF_BLUE        = HexColor("#2563eb")
CF_WHITE       = white


class CounterFlowPDFInvoice:
    """
    CounterFlow — PDF Invoice Generator.

    Generates a clean A4 invoice PDF for a finalized invoice.
    Saves the file to COUNTERFLOW_INVOICE_OUTPUT_DIR.

    Usage:
        generator = CounterFlowPDFInvoice()
        pdf_path  = generator.counterflow_generate(invoice)
        # Returns full path to the saved PDF
    """

    # Page margin in mm
    COUNTERFLOW_MARGIN = 20 * mm

    def __init__(self):
        os.makedirs(COUNTERFLOW_INVOICE_OUTPUT_DIR, exist_ok=True)

    def counterflow_generate(
        self,
        invoice: CounterFlowInvoice,
        open_after: bool = False,
    ) -> str:
        """
        CounterFlow — Generate a PDF invoice for a finalized invoice.

        Args:
            invoice:     The CounterFlowInvoice ORM object (with items loaded)
            open_after:  If True, opens the PDF after generation (Windows)

        Returns:
            Full path to the saved PDF file.
        """
        counterflow_filename = f"{invoice.counterflow_invoice_number}.pdf"
        counterflow_filepath = os.path.join(
            COUNTERFLOW_INVOICE_OUTPUT_DIR,
            counterflow_filename
        )

        counterflow_doc = SimpleDocTemplate(
            counterflow_filepath,
            pagesize=A4,
            rightMargin=self.COUNTERFLOW_MARGIN,
            leftMargin=self.COUNTERFLOW_MARGIN,
            topMargin=self.COUNTERFLOW_MARGIN,
            bottomMargin=self.COUNTERFLOW_MARGIN,
        )

        counterflow_story = self._counterflow_build_story(invoice)
        counterflow_doc.build(counterflow_story)

        if open_after:
            self._counterflow_open_file(counterflow_filepath)

        return counterflow_filepath

    # ── Story Builder ──────────────────────────────────────────

    def _counterflow_build_story(self, invoice: CounterFlowInvoice) -> list:
        """CounterFlow — Build the full PDF story (list of flowables)."""
        counterflow_styles = self._counterflow_get_styles()
        counterflow_story  = []

        # ── Header ─────────────────────────────────────────────
        counterflow_story.append(
            self._counterflow_build_header(counterflow_styles)
        )
        counterflow_story.append(Spacer(1, 6 * mm))

        # ── Divider ────────────────────────────────────────────
        counterflow_story.append(
            HRFlowable(
                width="100%",
                thickness=1,
                color=CF_BORDER,
                spaceAfter=6 * mm,
            )
        )

        # ── Invoice meta row ───────────────────────────────────
        counterflow_story.append(
            self._counterflow_build_meta(invoice, counterflow_styles)
        )
        counterflow_story.append(Spacer(1, 6 * mm))

        # ── Customer info ──────────────────────────────────────
        if invoice.counterflow_customer:
            counterflow_story.append(
                self._counterflow_build_customer(
                    invoice.counterflow_customer,
                    counterflow_styles
                )
            )
            counterflow_story.append(Spacer(1, 6 * mm))

        # ── Items table ────────────────────────────────────────
        counterflow_story.append(
            self._counterflow_build_items_table(invoice, counterflow_styles)
        )
        counterflow_story.append(Spacer(1, 6 * mm))

        # ── Totals ─────────────────────────────────────────────
        counterflow_story.append(
            self._counterflow_build_totals(invoice, counterflow_styles)
        )
        counterflow_story.append(Spacer(1, 8 * mm))

        # ── Footer ─────────────────────────────────────────────
        counterflow_story.append(
            HRFlowable(
                width="100%",
                thickness=1,
                color=CF_BORDER,
                spaceBefore=2 * mm,
                spaceAfter=4 * mm,
            )
        )
        counterflow_story.append(
            self._counterflow_build_footer(counterflow_styles)
        )

        return counterflow_story

    # ── Section Builders ───────────────────────────────────────

    def _counterflow_build_header(self, styles) -> Table:
        """CounterFlow — Top header: app name + tagline."""
        counterflow_name = Paragraph(
            f"<b>{COUNTERFLOW_APP_NAME}</b>",
            styles["cf_title"]
        )
        counterflow_tag = Paragraph(
            "Retail Management & Billing",
            styles["cf_subtitle"]
        )
        counterflow_invoice_lbl = Paragraph(
            "<b>INVOICE</b>",
            styles["cf_invoice_label"]
        )

        counterflow_data = [[counterflow_name, counterflow_invoice_lbl]]
        counterflow_table = Table(
            counterflow_data,
            colWidths=["70%", "30%"]
        )
        counterflow_table.setStyle(TableStyle([
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN",      (1, 0), (1, 0),   "RIGHT"),
        ]))
        return counterflow_table

    def _counterflow_build_meta(self, invoice, styles) -> Table:
        """CounterFlow — Invoice number, date, payment method row."""
        counterflow_method_color = {
            "CASH":   CF_SUCCESS,
            "UPI":    CF_BLUE,
            "CREDIT": CF_WARNING,
        }.get(invoice.counterflow_payment_method, CF_GRAY)

        counterflow_data = [
            [
                Paragraph(
                    f"<b>Invoice Number</b><br/>"
                    f"<font size='12'>{invoice.counterflow_invoice_number}</font>",
                    styles["cf_meta_left"]
                ),
                Paragraph(
                    f"<b>Date & Time</b><br/>"
                    f"{counterflow_format_datetime(invoice.counterflow_created_at)}",
                    styles["cf_meta_center"]
                ),
                Paragraph(
                    f"<b>Payment</b><br/>"
                    f"<font color='#{counterflow_method_color.hexval()[2:]}'>"
                    f"<b>{invoice.counterflow_payment_method}</b></font>",
                    styles["cf_meta_right"]
                ),
            ]
        ]

        counterflow_table = Table(
            counterflow_data,
            colWidths=["34%", "33%", "33%"]
        )
        counterflow_table.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, -1), CF_LIGHT_GRAY),
            ("ROUNDEDCORNERS", [6]),
            ("BOX",         (0, 0), (-1, -1), 1, CF_BORDER),
            ("INNERGRID",   (0, 0), (-1, -1), 0.5, CF_BORDER),
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",  (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ]))
        return counterflow_table

    def _counterflow_build_customer(self, customer, styles) -> Table:
        """CounterFlow — Customer information block."""
        counterflow_mobile_display = counterflow_format_mobile(
            customer.counterflow_mobile
        )
        counterflow_credit_line = ""
        if customer.counterflow_credit_balance > 0:
            counterflow_credit_line = (
                f"<br/>Outstanding Credit: "
                f"<font color='#d97706'>"
                f"<b>{counterflow_format_currency(customer.counterflow_credit_balance)}</b>"
                f"</font>"
            )

        counterflow_data = [[
            Paragraph(
                f"<b>Bill To</b><br/>"
                f"<font size='11'><b>{customer.counterflow_name}</b></font><br/>"
                f"<font color='#6b7280'>{counterflow_mobile_display}</font>"
                f"{counterflow_credit_line}",
                styles["cf_normal"]
            )
        ]]
        counterflow_table = Table(counterflow_data, colWidths=["100%"])
        counterflow_table.setStyle(TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ]))
        return counterflow_table

    def _counterflow_build_items_table(self, invoice, styles) -> Table:
        """CounterFlow — Line items table with header."""
        # Header row
        counterflow_header = [
            Paragraph("<b>#</b>",         styles["cf_table_header"]),
            Paragraph("<b>Product</b>",   styles["cf_table_header"]),
            Paragraph("<b>Unit Price</b>", styles["cf_table_header_right"]),
            Paragraph("<b>Qty</b>",        styles["cf_table_header_right"]),
            Paragraph("<b>Total</b>",      styles["cf_table_header_right"]),
        ]

        counterflow_rows = [counterflow_header]

        for i, item in enumerate(invoice.counterflow_items, 1):
            counterflow_rows.append([
                Paragraph(str(i), styles["cf_cell"]),
                Paragraph(
                    item.counterflow_product.counterflow_name,
                    styles["cf_cell"]
                ),
                Paragraph(
                    counterflow_format_currency(item.counterflow_unit_price),
                    styles["cf_cell_right"]
                ),
                Paragraph(
                    str(item.counterflow_quantity),
                    styles["cf_cell_right"]
                ),
                Paragraph(
                    counterflow_format_currency(item.counterflow_line_total),
                    styles["cf_cell_right"]
                ),
            ])

        counterflow_table = Table(
            counterflow_rows,
            colWidths=["8%", "44%", "18%", "10%", "20%"],
        )
        counterflow_table.setStyle(TableStyle([
            # Header
            ("BACKGROUND",    (0, 0), (-1, 0),  CF_BLACK),
            ("TEXTCOLOR",     (0, 0), (-1, 0),  CF_WHITE),
            ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, 0),  9),
            ("TOPPADDING",    (0, 0), (-1, 0),  8),
            ("BOTTOMPADDING", (0, 0), (-1, 0),  8),
            # Data rows
            ("FONTNAME",      (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",      (0, 1), (-1, -1), 9),
            ("TOPPADDING",    (0, 1), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
            # Alternating rows
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [CF_WHITE, CF_LIGHT_GRAY]),
            # Grid
            ("LINEBELOW",     (0, 0), (-1, -1), 0.5, CF_BORDER),
            ("BOX",           (0, 0), (-1, -1), 1,   CF_BORDER),
            # Padding
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return counterflow_table

    def _counterflow_build_totals(self, invoice, styles) -> Table:
        """CounterFlow — Totals block on the right side."""
        counterflow_total_color = CF_BLACK

        counterflow_data = [
            [
                "",
                Paragraph("Subtotal", styles["cf_total_label"]),
                Paragraph(
                    counterflow_format_currency(invoice.counterflow_total_amount),
                    styles["cf_total_value"]
                ),
            ],
            [
                "",
                Paragraph("Tax (0%)", styles["cf_total_label"]),
                Paragraph("₹0.00", styles["cf_total_value"]),
            ],
            [
                "",
                Paragraph("<b>Grand Total</b>", styles["cf_grand_label"]),
                Paragraph(
                    f"<b>{counterflow_format_currency(invoice.counterflow_total_amount)}</b>",
                    styles["cf_grand_value"]
                ),
            ],
        ]

        counterflow_table = Table(
            counterflow_data,
            colWidths=["50%", "30%", "20%"],
        )
        counterflow_table.setStyle(TableStyle([
            ("ALIGN",         (2, 0), (2, -1), "RIGHT"),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            # Grand total row highlight
            ("BACKGROUND",    (1, 2), (2, 2), CF_LIGHT_GRAY),
            ("LINEABOVE",     (1, 2), (2, 2), 1, CF_BORDER),
            ("TOPPADDING",    (0, 2), (-1, 2), 8),
            ("BOTTOMPADDING", (0, 2), (-1, 2), 8),
            ("LEFTPADDING",   (1, 0), (1, -1), 12),
            ("RIGHTPADDING",  (2, 0), (2, -1), 12),
        ]))
        return counterflow_table

    def _counterflow_build_footer(self, styles) -> Paragraph:
        """CounterFlow — Footer with thank you message and branding."""
        return Paragraph(
            f"Thank you for your business!  •  "
            f"Generated by {COUNTERFLOW_APP_NAME} v{COUNTERFLOW_VERSION}  •  "
            f"by CN-6",
            styles["cf_footer"]
        )

    # ── Styles ─────────────────────────────────────────────────

    def _counterflow_get_styles(self) -> dict:
        """CounterFlow — Returns all paragraph styles used in the invoice."""
        return {
            "cf_title": ParagraphStyle(
                "cf_title",
                fontSize=18,
                fontName="Helvetica-Bold",
                textColor=CF_BLACK,
                spaceAfter=2,
            ),
            "cf_subtitle": ParagraphStyle(
                "cf_subtitle",
                fontSize=9,
                fontName="Helvetica",
                textColor=CF_GRAY,
            ),
            "cf_invoice_label": ParagraphStyle(
                "cf_invoice_label",
                fontSize=20,
                fontName="Helvetica-Bold",
                textColor=CF_GRAY,
                alignment=TA_RIGHT,
            ),
            "cf_meta_left": ParagraphStyle(
                "cf_meta_left",
                fontSize=9,
                fontName="Helvetica",
                textColor=CF_BLACK,
                alignment=TA_LEFT,
                leading=14,
            ),
            "cf_meta_center": ParagraphStyle(
                "cf_meta_center",
                fontSize=9,
                fontName="Helvetica",
                textColor=CF_BLACK,
                alignment=TA_CENTER,
                leading=14,
            ),
            "cf_meta_right": ParagraphStyle(
                "cf_meta_right",
                fontSize=9,
                fontName="Helvetica",
                textColor=CF_BLACK,
                alignment=TA_RIGHT,
                leading=14,
            ),
            "cf_normal": ParagraphStyle(
                "cf_normal",
                fontSize=9,
                fontName="Helvetica",
                textColor=CF_BLACK,
                leading=14,
            ),
            "cf_table_header": ParagraphStyle(
                "cf_table_header",
                fontSize=9,
                fontName="Helvetica-Bold",
                textColor=CF_WHITE,
                alignment=TA_LEFT,
            ),
            "cf_table_header_right": ParagraphStyle(
                "cf_table_header_right",
                fontSize=9,
                fontName="Helvetica-Bold",
                textColor=CF_WHITE,
                alignment=TA_RIGHT,
            ),
            "cf_cell": ParagraphStyle(
                "cf_cell",
                fontSize=9,
                fontName="Helvetica",
                textColor=CF_BLACK,
                alignment=TA_LEFT,
            ),
            "cf_cell_right": ParagraphStyle(
                "cf_cell_right",
                fontSize=9,
                fontName="Helvetica",
                textColor=CF_BLACK,
                alignment=TA_RIGHT,
            ),
            "cf_total_label": ParagraphStyle(
                "cf_total_label",
                fontSize=9,
                fontName="Helvetica",
                textColor=CF_GRAY,
                alignment=TA_LEFT,
            ),
            "cf_total_value": ParagraphStyle(
                "cf_total_value",
                fontSize=9,
                fontName="Helvetica",
                textColor=CF_BLACK,
                alignment=TA_RIGHT,
            ),
            "cf_grand_label": ParagraphStyle(
                "cf_grand_label",
                fontSize=11,
                fontName="Helvetica-Bold",
                textColor=CF_BLACK,
                alignment=TA_LEFT,
            ),
            "cf_grand_value": ParagraphStyle(
                "cf_grand_value",
                fontSize=11,
                fontName="Helvetica-Bold",
                textColor=CF_BLACK,
                alignment=TA_RIGHT,
            ),
            "cf_footer": ParagraphStyle(
                "cf_footer",
                fontSize=8,
                fontName="Helvetica",
                textColor=CF_GRAY,
                alignment=TA_CENTER,
            ),
        }

    # ── Helpers ────────────────────────────────────────────────

    @staticmethod
    def _counterflow_open_file(filepath: str):
        """CounterFlow — Open a file with the OS default application."""
        import subprocess, sys
        try:
            if sys.platform == "win32":
                os.startfile(filepath)
            elif sys.platform == "darwin":
                subprocess.run(["open", filepath], check=False)
            else:
                subprocess.run(["xdg-open", filepath], check=False)
        except Exception:
            pass  # Silent fail — file was still saved correctly

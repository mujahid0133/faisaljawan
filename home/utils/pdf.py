# utils/pdf.py
import io
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Flowable
)
from reportlab.lib.units import cm, mm


class BoxPlaceholder(Flowable):
    """Draw an empty framed box (used as the FBR logo placeholder)."""

    def __init__(self, width, height, stroke=1, dash=None):
        super().__init__()
        self.width = width
        self.height = height
        self.stroke = stroke
        self.dash = dash

    def wrap(self, availWidth, availHeight):
        return (self.width, self.height)

    def draw(self):
        if self.dash:
            self.canv.setDash(self.dash)
        self.canv.setLineWidth(self.stroke)
        self.canv.rect(0, 0, self.width, self.height)


def generate_invoice_pdf(invoice, special_case=""):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )

    styles = getSampleStyleSheet()
    # --- Custom styles (readable on A4) ---
    title = ParagraphStyle(
        "TitleBig", parent=styles["Title"], fontSize=18, leading=22,
        alignment=1, spaceAfter=2
    )
    subtitle_chip = ParagraphStyle(
        "Chip", parent=styles["Normal"], fontSize=9.5, leading=12,
        alignment=1, textColor=colors.white
    )
    normal = ParagraphStyle(
        "Normal10", parent=styles["Normal"], fontSize=10.5, leading=13.5
    )
    small = ParagraphStyle(
        "Small", parent=styles["Normal"], fontSize=9, leading=12
    )
    tbl_header = ParagraphStyle(
        "TblHeader", parent=styles["Normal"], fontSize=9.5, leading=12, alignment=1
    )
    tbl_small = ParagraphStyle(
        "TblSmall", parent=styles["Normal"], fontSize=8.7, leading=11
    )
    tbl_small_right = ParagraphStyle(
        "TblSmallRight", parent=tbl_small, alignment=2  # right
    )
    tbl_small_center = ParagraphStyle(
        "TblSmallCenter", parent=tbl_small, alignment=1
    )

    elements = []

    # ========== HEADER ==========
    elements.append(Paragraph("M. FAZAL ELLAHI & SONS", title))

    # black chip (AUTOMOBILE ENGINEER)
    chip_tbl = Table(
        [[Paragraph("<b>AUTOMOBILE ENGINEER</b>", subtitle_chip)]],
        colWidths=[70 * mm],
        hAlign="CENTER",
        style=[
            ("BACKGROUND", (0, 0), (-1, -1), colors.black),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("INNERPADDING", (0, 0), (-1, -1), 2),
            ("BOX", (0, 0), (-1, -1), 0.8, colors.black),
        ],
    )
    elements.append(chip_tbl)
    elements.append(Spacer(1, 6))

    # Address / contact / tax numbers (hardcoded, centered)
    header_lines = [
        "Behind Dyal Singh Mansion, The Mall, Lahore.",
        "TEL: 0321-3434343, 0321-3434343",
        "NTN : 1015078-1 &nbsp;&nbsp;&nbsp; STRN: 1015078-1 &nbsp;&nbsp;&nbsp; PRA: 1015078-1",
    ]
    for line in header_lines:
        elements.append(Paragraph(line, small))
    elements.append(Spacer(1, 8))

    # ========== INVOICE #: & DATE ==========
    info_tbl = Table(
        [[
            Paragraph("<b>INVOICE #:</b>", normal),
            Paragraph(
                f"{invoice.prefix if hasattr(invoice,'prefix') and invoice.prefix else ''}{special_case}{invoice.invoice_no}", normal),
            Paragraph("<b>Date:</b>", normal),
            Paragraph(invoice.date.strftime("%d-%m-%Y"), normal),
        ]],
        colWidths=[25*mm, 60*mm, 20*mm, 50*mm],
        style=[
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ],
        hAlign="LEFT",
    )
    elements.append(info_tbl)
    elements.append(Spacer(1, 8))

    # ========== COMPANY & VEHICLE DETAIL ==========
    # Section headers row ("Company Detail" | "Vehicle Detail")
    sec_hdr = Table(
        [[
            Paragraph("<b>COMPANY DETAIL</b>", tbl_header),
            Paragraph("<b>Vehicle Detail</b>", tbl_header),
        ]],
        colWidths=[80*mm, 80*mm],
        style=[
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ],
    )
    elements.append(sec_hdr)

    # Two-column details box (each cell wraps words only)
    comp_rows = [
        [Paragraph("<b>Name :</b>", small),
         Paragraph(invoice.customer.name or "", small)],
        [Paragraph("<b>Address :</b>", small),
         Paragraph(invoice.customer.address or "", small)],
        [Paragraph("<b>STRN :</b>", small), Paragraph(invoice.customer.srtn or (
            getattr(invoice.customer, "strn", "") or ""), small)],
        [Paragraph("<b>NTN :</b>", small),
         Paragraph(invoice.customer.ntn or "", small)],
    ]
    veh_rows = [
        [Paragraph("<b>Make :</b>", small),
         Paragraph(getattr(invoice.vehicle, "make", "") or "", small)],
        [Paragraph("<b>Vehicle-Number :</b>", small),
         Paragraph(getattr(invoice.vehicle, "number", "") or "", small)],
        [Paragraph("<b>Customer Name:</b>", small), Paragraph(getattr(invoice,
                                                                      "customer_name", "") or (invoice.customer.name or ""), small)],
        [Paragraph("<b>Customer No:</b>", small),
         Paragraph(getattr(invoice.customer, "phone", "") or "", small)],
    ]

    def boxed_grid(rows):
        t = Table(
            rows, colWidths=[28*mm, 52*mm],
            style=[
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ],
        )
        return t

    two_col = Table(
        [[boxed_grid(comp_rows), boxed_grid(veh_rows)]],
        colWidths=[80*mm, 80*mm],
        style=[("VALIGN", (0, 0), (-1, -1), "TOP")],
        hAlign="LEFT",
    )
    elements.append(two_col)
    elements.append(Spacer(1, 8))

    # ========== ITEMS TABLE (extended, readable, description wider) ==========
    # Keep your 9 columns, but make Description wide and everything wrap.
    header_row = [
        Paragraph("<b>No.</b>", tbl_small_center),
        Paragraph("<b>Description</b>", tbl_small_center),
        Paragraph("<b>QTY</b>", tbl_small_center),
        Paragraph("<b>Unit Price</b>", tbl_small_center),
        Paragraph("<b>Amount</b>", tbl_small_center),
        Paragraph("<b>Tax %</b>", tbl_small_center),
        Paragraph("<b>Tax Amt</b>", tbl_small_center),
        Paragraph("<b>Total</b>", tbl_small_center),
    ]
    data = [header_row]

    # Filter items for each bill type
    filtered_items = []
    for item in invoice.items.all():
        if special_case == "F-":
            if item.category and item.category.name.lower() != "goods":
                continue
        elif special_case == "P-":
            if item.category and item.category.name.lower() != "service":
                continue
        filtered_items.append(item)

    # Calculate totals for filtered items
    subtotal = sum(item.price_excl_tax * item.qty for item in filtered_items)
    total_tax = sum(item.tax_amount for item in filtered_items)
    grand_total = sum(item.price_incl_tax for item in filtered_items)

    idx = 0
    for item in filtered_items:
        idx += 1
        row = [
            Paragraph(str(idx), tbl_small_center),
            Paragraph(item.product.name or "", tbl_small),
            Paragraph(str(item.qty), tbl_small_right),
            Paragraph(f"{item.price_excl_tax:.2f}", tbl_small_right),
            Paragraph(f"{(item.price_excl_tax * item.qty):.2f}",
                      tbl_small_right),
            Paragraph(f"{item.category.rate:.2f}%", tbl_small_right) if item.category else Paragraph(
                "-", tbl_small_right),
            Paragraph(f"{item.tax_amount:.2f}", tbl_small_right),
            Paragraph(f"{item.price_incl_tax:.2f}", tbl_small_right),
        ]
        data.append(row)

    items_tbl = Table(
        data,
        colWidths=[
            10*mm,   # No.
            55*mm,   # Description (WIDE)
            12*mm,   # QTY
            22*mm,   # Unit Price
            25*mm,   # Amount
            15*mm,   # Tax %
            22*mm,   # Tax Amt
            22*mm,   # Total
        ],
        repeatRows=1,
        style=[
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ],
        hAlign="LEFT",
    )
    elements.append(items_tbl)
    elements.append(Spacer(1, 8))

    # ========== TOTALS (keep your existing code behavior) ==========
    totals_tbl = Table(
        [
            [Paragraph("<b>Subtotal</b>", normal),
             Paragraph(f"{subtotal:.2f}", tbl_small_right)],
            [Paragraph("<b>Total Tax</b>", normal),
             Paragraph(f"{total_tax:.2f}", tbl_small_right)],
            [Paragraph("<b>Grand Total</b>", normal),
             Paragraph(f"{grand_total:.2f}", tbl_small_right)],
        ],
        colWidths=[140*mm, 20*mm],
        style=[
            ("BOX", (0, 0), (-1, -1), 1, colors.black),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ],
        hAlign="RIGHT",
    )
    elements.append(totals_tbl)
    elements.append(Spacer(1, 12))

    # ========== SIGNATURE LINE ==========
    elements.append(Paragraph("Signature:", normal))
    # draw a line using an empty table cell border for perfect alignment
    sign_tbl = Table(
        [[" "]],
        colWidths=[70*mm],
        style=[("LINEBELOW", (0, 0), (-1, -1), 0.7, colors.black)],
    )
    elements.append(sign_tbl)
    elements.append(Spacer(1, 8))

    # ========== FOOTER (disclaimer left, FBR placeholder right) ==========
    disclaimer = Paragraph(
        "Customer’s vehicle driven and stored entirely at customer’s own risk at repair firm; theft, damage, or loss is not the firm’s responsibility.",
        tbl_small
    )
    fbr_box = Table(
        [[BoxPlaceholder(40*mm, 18*mm)]],
        colWidths=[40*mm],
        style=[("BOX", (0, 0), (-1, -1), 0.8, colors.black)],
        hAlign="RIGHT",
    )
    fbr_num = Paragraph(
        f"FBR Invoice Number: {getattr(invoice, 'invoice_no', '')}",
        tbl_small_center,
    )

    footer = Table(
        [
            [disclaimer, ""],
            ["", fbr_box],
            ["", fbr_num],
        ],
        colWidths=[120*mm, 40*mm],
        style=[
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ],
        hAlign="LEFT",
    )
    elements.append(footer)

    # Build & return
    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{invoice.invoice_no}.pdf"'
    return response

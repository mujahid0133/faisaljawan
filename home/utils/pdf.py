# utils/pdf.py
import io
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import cm


def generate_invoice_pdf(invoice):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20,
    )

    elements = []
    styles = getSampleStyleSheet()

    # --- Header (Seller Info) ---
    elements.append(
        Paragraph(
            "<b>M. Fazal Ellahi & Sons</b><br/>"
            "NTN: 1234567-8<br/>GST: 9876543-2",
            styles["Normal"],
        )
    )
    elements.append(Spacer(1, 12))

    # --- Invoice No / Date ---
    invoice_info = [
        ["Invoice No:", invoice.invoice_no, "Date:", invoice.date.strftime("%d-%m-%Y")],
    ]
    t = Table(
        invoice_info,
        colWidths=[2.5 * cm, 6 * cm, 2.5 * cm, 6 * cm],
    )
    t.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )
    elements.append(t)
    elements.append(Spacer(1, 12))

    # --- Customer & Vehicle Info ---
    cust_info = [
        ["Customer:", invoice.customer.name, "Vehicle:", invoice.vehicle.number],
        ["Address:", invoice.customer.address or "", "NTN:", invoice.customer.ntn or ""],
    ]
    t = Table(
        cust_info,
        colWidths=[2.5 * cm, 6 * cm, 2.5 * cm, 6 * cm],
    )
    t.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )
    elements.append(t)
    elements.append(Spacer(1, 12))

    # --- Product Table ---
    data = [
        ["S.No", "HS Code", "Description", "Qty", "Unit Price", "Amount", "Tax %", "Tax Amt", "Total"]
    ]
    for idx, item in enumerate(invoice.items.all(), start=1):
        data.append(
            [
                str(idx),
                item.product.hs_code or "",
                item.product.name,
                str(item.qty),
                f"{item.price_excl_tax:.2f}",
                f"{item.price_excl_tax * item.qty:.2f}",
                f"{item.gst_rate:.2f}%",   # ✅ fixed here
                f"{item.tax_amount:.2f}",
                f"{item.price_incl_tax:.2f}",
            ]
        )
    table = Table(
        data,
        colWidths=[1.2 * cm, 2.2 * cm, 5 * cm, 1.2 * cm, 2.2 * cm, 2.5 * cm, 1.5 * cm, 2.5 * cm, 2.5 * cm],
    )
    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("ALIGN", (3, 1), (-1, -1), "RIGHT"),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 12))

    # --- Totals ---
    totals_data = [
        ["Subtotal", f"{invoice.total_excl_tax:.2f}"],
        ["Total Tax", f"{invoice.total_tax:.2f}"],
        ["Grand Total", f"{invoice.total_incl_tax:.2f}"],
    ]
    t = Table(totals_data, colWidths=[14 * cm, 4 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 1, colors.black),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ]
        )
    )
    elements.append(t)
    elements.append(Spacer(1, 24))

    # --- Signature ---
    elements.append(Paragraph("<br/><br/>Authorized Signatory ____________________", styles["Normal"]))

    # Build PDF
    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{invoice.invoice_no}.pdf"'
    return response

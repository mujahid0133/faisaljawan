
from django.template.loader import get_template
from django.http import HttpResponse
import io
from .models import Invoice
from django.shortcuts import render
from xhtml2pdf import pisa


def invoice_pdf(request, pk):
    invoice = Invoice.objects.get(pk=pk)
    template = get_template("invoice_pdf.html")
    html = template.render({"invoice": invoice})

    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result)

    if pisa_status.err:
        # Optionally, render the HTML for debugging if PDF fails
        return render(request, "invoice_pdf.html", {"invoice": invoice, "pdf_error": True})

    response = HttpResponse(result.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="Invoice_{invoice.invoice_no}.pdf"'
    return response

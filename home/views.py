from .models import Invoice
from django.shortcuts import render


def invoice_pdf(request, pk):
    invoice = Invoice.objects.get(pk=pk)
    return render(request, "index.html", {"invoice": invoice})

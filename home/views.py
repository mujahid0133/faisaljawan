from .models import Invoice
from django.shortcuts import render
from django.db.models import Prefetch
from django.utils import timezone

# Bill report view: show all invoices in a table


def bill_report(request):
    ids = request.GET.get('ids')
    qs = Invoice.objects.select_related('customer', 'vehicle').prefetch_related(
        'items__product', 'items__category')
    if ids:
        id_list = [int(i) for i in ids.split(',') if i.isdigit()]
        qs = qs.filter(id__in=id_list)
    grand_total = sum(inv.total_incl_tax for inv in qs)
    customer_ids = set(inv.customer_id for inv in qs)
    single_customer_name = None
    if len(customer_ids) == 1 and qs:
        single_customer_name = qs[0].customer.name
    current_date = timezone.now()
    return render(
        request,
        "billreport.html",
        {
            "invoices": qs,
            "grand_total": grand_total,
            "single_customer_name": single_customer_name,
            "current_date": current_date,  # <-- Add this line
        }
    )


def invoice_pdf(request, pk):
    invoice = Invoice.objects.get(pk=pk)
    # Default: no special case
    return _render_invoice_html(request, invoice, special_case=None)


def invoice_pdf_goods(request, pk):
    invoice = Invoice.objects.get(pk=pk)
    return _render_invoice_html(request, invoice, special_case="goods")


def invoice_pdf_services(request, pk):
    invoice = Invoice.objects.get(pk=pk)
    return _render_invoice_html(request, invoice, special_case="services")


def _render_invoice_html(request, invoice, special_case=None):
    # Filter items for each bill type
    filtered_items = []
    for item in invoice.items.all():
        if special_case == "goods":
            if item.category and item.category.name.lower() != "goods":
                continue
        elif special_case == "services":
            if item.category and item.category.name.lower() != "service":
                continue
        filtered_items.append(item)

    # Calculate totals for filtered items
    subtotal = sum(item.price_excl_tax * item.qty for item in filtered_items)
    total_tax = sum(item.tax_amount for item in filtered_items)
    grand_total = sum(item.price_incl_tax for item in filtered_items)

    return render(request, "index.html", {
        "invoice": invoice,
        "items": filtered_items,
        "subtotal": subtotal,
        "total_tax": total_tax,
        "grand_total": grand_total,
        "special_case": special_case,
    })

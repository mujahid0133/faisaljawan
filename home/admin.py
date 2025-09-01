from django.contrib import admin
from .models import Customer, Vehicle, Product, Invoice, InvoiceItem

from django.utils.html import format_html
import csv
from django.http import HttpResponse
from django.urls import path
from django.shortcuts import get_object_or_404

from .utils.pdf import generate_invoice_pdf


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    exclude = ("description", "price_excl_tax",
               "gst_rate", "tax_amount", "price_incl_tax")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "srtn", "ntn")
    search_fields = ("name", "address", "srtn", "ntn")


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("make", "number", "customer")
    search_fields = ("make", "number", "customer__name")
    list_filter = ("make",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "hs_code", "price_excl_tax", "gst_rate")
    search_fields = ("name", "hs_code")


# --- Actions ---
def export_invoices_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="invoices.csv"'
    writer = csv.writer(response)
    writer.writerow(["Invoice No", "Customer", "Vehicle",
                    "Date", "Total Incl Tax (PKR)", "Status"])
    for inv in queryset:
        writer.writerow([
            inv.invoice_no, inv.customer.name, inv.vehicle.number,
            inv.date.strftime("%Y-%m-%d %H:%M"),
            inv.total_incl_tax, inv.status
        ])
    return response


export_invoices_csv.short_description = "Export selected invoices to CSV"


def mark_as_paid(modeladmin, request, queryset):
    queryset.update(status="paid")


def mark_as_unpaid(modeladmin, request, queryset):
    queryset.update(status="unpaid")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    inlines = [InvoiceItemInline]

    list_display = (
        "invoice_no", "customer", "vehicle",
        "date", "status", "formatted_total", "print_button"
    )
    list_filter = ("status", "date", "customer", "vehicle")
    search_fields = ("invoice_no", "customer__name", "vehicle__number")
    exclude = ("status", "total_excl_tax", "total_tax", "total_incl_tax")
    actions = [mark_as_paid, mark_as_unpaid, export_invoices_csv]

    def formatted_total(self, obj):
        return format_html("₨ {}", f"{obj.total_incl_tax:.2f}")
    formatted_total.short_description = "Total (PKR)"

    # ✅ Print button
    def print_button(self, obj):
        return format_html('<a class="button" href="{}">Print PDF</a>',
                           f"/admin/home/invoice/{obj.id}/print/")
    print_button.short_description = "Print Invoice"

    # ✅ Add custom URL for printing
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("<int:invoice_id>/print/", self.admin_site.admin_view(self.print_invoice),
                 name="invoice-print"),
        ]
        return custom_urls + urls

    def print_invoice(self, request, invoice_id, *args, **kwargs):
        invoice = get_object_or_404(Invoice, pk=invoice_id)
        return generate_invoice_pdf(invoice)

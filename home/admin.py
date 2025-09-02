from django.contrib import admin
from .models import Customer, Vehicle, Product, Invoice, InvoiceItem, Taxes

from django.utils.html import format_html
import csv
from django.http import HttpResponse
from django.urls import path
from django.shortcuts import get_object_or_404

from .utils.pdf import generate_invoice_pdf


# SPECIAL_CASES = {
    
# }



class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1
    exclude = ("description", "tax_amount", "price_incl_tax", "category")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "srtn", "ntn")
    search_fields = ("name", "address", "srtn", "ntn")


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("make", "number", "customer")
    search_fields = ("make", "number", "customer__name")
    list_filter = ("make",)


@admin.register(Taxes)
class TaxAdmin(admin.ModelAdmin):
    list_display = ("name", "rate")
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price_excl_tax", "category")
    search_fields = ("name",)
    exclude = ("hs_code",)


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
        "date", "status", "formatted_total", "print_complete_bill", "print_fbr_bill", "print_pra_bill"
    )
    list_filter = ("status", "date", "customer", "vehicle")
    search_fields = ("invoice_no", "customer__name", "vehicle__number")
    exclude = ("status", "total_excl_tax", "total_tax", "total_incl_tax")
    actions = [mark_as_paid, mark_as_unpaid, export_invoices_csv]

    def formatted_total(self, obj):
        return format_html("₨ {}", f"{obj.total_incl_tax:.2f}")
    formatted_total.short_description = "Total (PKR)"

    # ✅ Print button
    def print_complete_bill(self, obj):
        return format_html('<a class="button" href="{}">Complete Bill</a>',
                           f"/admin/home/invoice/{obj.id}/C-/print/")
    print_complete_bill.short_description = "Print Complete Bill"

    def print_fbr_bill(self, obj):
        return format_html('<a class="button" href="{}">FBR Bill</a>',
                           f"/admin/home/invoice/{obj.id}/F-/print/")
    print_fbr_bill.short_description = "Print FBR Bill"

    def print_pra_bill(self, obj):
        return format_html('<a class="button" href="{}">PRA Bill</a>',
                           f"/admin/home/invoice/{obj.id}/P-/print/")
    print_pra_bill.short_description = "Print PRA Bill"

    # ✅ Add custom URL for printing
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("<int:invoice_id>/<str:special_case>/print/", self.admin_site.admin_view(self.print_invoice),
                 name="invoice-print"),

        ]
        return custom_urls + urls

    def print_invoice(self, request, invoice_id, special_case, *args, **kwargs):
        invoice = get_object_or_404(Invoice, pk=invoice_id)
        return generate_invoice_pdf(invoice, special_case)

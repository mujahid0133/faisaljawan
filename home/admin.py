from django.contrib import admin
from .models import Customer, Vehicle, Product, Invoice, InvoiceItem, Taxes

from django.utils.html import format_html
import csv
from django.http import HttpResponse, HttpResponseRedirect
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

# Batch action: Show selected invoices in bill report
def show_invoices_billreport(modeladmin, request, queryset):
    ids = queryset.values_list('id', flat=True)
    id_str = ','.join(str(i) for i in ids)
    return HttpResponseRedirect(f"/billreport/?ids={id_str}")


show_invoices_billreport.short_description = "Show selected invoices in Bill Report"


def mark_as_paid(modeladmin, request, queryset):
    queryset.update(status="paid")


def mark_as_unpaid(modeladmin, request, queryset):
    queryset.update(status="unpaid")

def download_complete_bill(modeladmin, request, queryset):
    links = [
        f"/invoice/{invoice.id}/pdf/?directdownload=true"
        for invoice in queryset
    ]

    # Generate a simple HTML with JS to open all links
    html = "<script>"
    for link in links:
        html += f"window.open('{link}', '_blank');"
    html += "window.history.back();</script>"

    return HttpResponse(html)

download_complete_bill.short_description = "Download Complete Bill for selected invoices"

def download_fbr_bill(modeladmin, request, queryset):
    links = [
        f"/invoice/{invoice.id}/pdf/goods/?directdownload=true"
        for invoice in queryset
    ]
    html = "<script>"
    for link in links:
        html += f"window.open('{link}', '_blank');"
    html += "window.history.back();</script>"

    return HttpResponse(html)

download_fbr_bill.short_description = "Download FBR Bill (Goods) for selected invoices"

def download_pra_bill(modeladmin, request, queryset):
    links = [
        f"/invoice/{invoice.id}/pdf/services/?directdownload=true"
        for invoice in queryset
    ]

    # Generate a simple HTML with JS to open all links
    html = "<script>"
    for link in links:
        html += f"window.open('{link}', '_blank');"
    html += "window.history.back();</script>"

    return HttpResponse(html)
download_pra_bill.short_description = "Download PRA Bill (Services) for selected invoices"


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    inlines = [InvoiceItemInline]
    date_hierarchy = "date"

    list_display = (
        "invoice_no", "customer", "vehicle",
        "date",
        # "status",
        "formatted_total", "print_complete_bill", "print_fbr_bill", "print_pra_bill"
    )
    list_filter = ("status", "date", "customer", "vehicle")
    search_fields = ("invoice_no", "customer__name", "vehicle__number")
    exclude = ("status", "total_excl_tax", "total_tax", "total_incl_tax")
    actions = [mark_as_paid, mark_as_unpaid, show_invoices_billreport, download_complete_bill, download_fbr_bill, download_pra_bill]

    def formatted_total(self, obj):
        return format_html("₨ {}", f"{obj.total_incl_tax:.2f}")
    formatted_total.short_description = "Total (PKR)"

    # SVG icons for reuse
    from django.utils.safestring import mark_safe
    EYE_SVG = mark_safe(
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" '
        'class="bi bi-eye" viewBox="0 0 16 16">'
        '<path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM8 13c-3.866 0-7-4-7-5s3.134-5 7-5 7 4 7 5-3.134 5-7 5z"/>'
        '<path d="M8 5a3 3 0 1 0 0 6 3 3 0 0 0 0-6z"/>'
        '<path d="M8 6.5a1.5 1.5 0 1 1 0 3 1.5 1.5 0 0 1 0-3z"/>'
        '</svg>'
    )
    DOWNLOAD_SVG = mark_safe(
        '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-download">'
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>'
        '<polyline points="7 10 12 15 17 10"></polyline>'
        '<line x1="12" y1="15" x2="12" y2="3"></line>'
        '</svg>'
    )

    def print_complete_bill(self, obj):
        return format_html(
            '<a class="button" href="{}" style="display: inline-flex; align-items: center; justify-content: center; margin-right: 5px">{}</a>'
            '<a class="button" href="{}?directdownload=true" target="_blank" style="display: inline-flex; align-items: center; justify-content: center;">{}</a>',
            f"/invoice/{obj.id}/pdf/", self.EYE_SVG,
            f"/invoice/{obj.id}/pdf/", self.DOWNLOAD_SVG
        )
    print_complete_bill.short_description = "Complete Bill"

    def print_fbr_bill(self, obj):
        return format_html(
            '<a class="button" href="{}" style="display: inline-flex; align-items: center; justify-content: center; margin-right: 5px">{}</a>'
            '<a class="button" href="{}?directdownload=true" target="_blank" style="display: inline-flex; align-items: center; justify-content: center;">{}</a>',
            f"/invoice/{obj.id}/pdf/goods/", self.EYE_SVG,
            f"/invoice/{obj.id}/pdf/goods/", self.DOWNLOAD_SVG
        )
    print_fbr_bill.short_description = "FBR Bill (Goods)"

    def print_pra_bill(self, obj):
        return format_html(
            '<a class="button" href="{}" style="display: inline-flex; align-items: center; justify-content: center; margin-right: 5px">{}</a>'
            '<a class="button" href="{}?directdownload=true" target="_blank" style="display: inline-flex; align-items: center; justify-content: center;">{}</a>',
            f"/invoice/{obj.id}/pdf/services/", self.EYE_SVG,
            f"/invoice/{obj.id}/pdf/services/", self.DOWNLOAD_SVG
        )
    print_pra_bill.short_description = "PRA Bill (Services)"

    # # ✅ Add custom URL for printing
    # def get_urls(self):
    #     urls = super().get_urls()
    #     custom_urls = [
    #         path("<int:invoice_id>/<str:special_case>/print/", self.admin_site.admin_view(self.print_invoice),
    #              name="invoice-print"),

    #     ]
    #     return custom_urls + urls

    # def print_invoice(self, request, invoice_id, special_case, *args, **kwargs):
    #     invoice = get_object_or_404(Invoice, pk=invoice_id)
    #     return generate_invoice_pdf(invoice, special_case)

from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


class Customer(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    srtn = models.CharField(max_length=50, blank=True, null=True)
    ntn = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name or "Unnamed Customer"


class Vehicle(models.Model):
    customer = models.ForeignKey(
        Customer, related_name="vehicles", on_delete=models.CASCADE)
    make = models.CharField(max_length=50)
    number = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.make} ({self.number})"


CATEGORY_CHOICES = [
    ("goods", "Goods"),
    ("service", "Service"),
]


class Product(models.Model):
    name = models.CharField(max_length=255)
    hs_code = models.CharField(max_length=50, blank=True, null=True)
    price_excl_tax = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey('Taxes', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name


class Invoice(models.Model):
    STATUS_CHOICES = [
        ("unpaid", "Unpaid"),
        ("paid", "Paid"),
        ("partial", "Partially Paid"),
    ]

    invoice_no = models.CharField(max_length=50, unique=True, editable=False)
    date = models.DateTimeField(default=timezone.now)

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="unpaid")

    total_excl_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_incl_tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Auto-generate invoice number
        if not self.invoice_no:
            last_invoice = Invoice.objects.order_by("-id").first()
            if last_invoice and last_invoice.invoice_no.startswith("MFES"):
                last_no = int(last_invoice.invoice_no.replace("MFES", ""))
                self.invoice_no = f"MFES{last_no+1:05d}"
            else:
                self.invoice_no = "MFES00001"
        super().save(*args, **kwargs)

    def update_totals(self):
        self.total_excl_tax = sum(item.price_excl_tax * item.qty for item in self.items.all())
        self.total_tax = sum(item.tax_amount for item in self.items.all())
        self.total_incl_tax = sum(item.price_incl_tax for item in self.items.all())
        super().save(update_fields=["total_excl_tax", "total_tax", "total_incl_tax"])

    def __str__(self):
        return f"{self.invoice_no} - {self.customer.name}"

class Taxes(models.Model):
    name = models.CharField(max_length=100 , choices=CATEGORY_CHOICES)
    rate = models.DecimalField(max_digits=5, decimal_places=2)
    def __str__(self):
        return f"{self.name}"

class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=True, null=True)
    qty = models.IntegerField(default=1)

    price_excl_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    category = models.ForeignKey(Taxes, on_delete=models.SET_NULL, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_incl_tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if self.product:
            self.price_excl_tax = self.product.price_excl_tax
            self.category = self.product.category
        self.tax_amount = (self.price_excl_tax * self.qty) * (self.category.rate / 100)
        self.price_incl_tax = (self.price_excl_tax * self.qty) + self.tax_amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} ({self.qty})"


# --- Signals ---
@receiver(post_save, sender=InvoiceItem)
@receiver(post_delete, sender=InvoiceItem)
def update_invoice_totals(sender, instance, **kwargs):
    instance.invoice.update_totals()

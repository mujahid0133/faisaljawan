from decimal import Decimal
import random
from django.utils import timezone
from home.models import Customer, Vehicle, Product, Taxes, Invoice, InvoiceItem

goods, _ = Taxes.objects.get_or_create(
    name="goods", defaults={"rate": Decimal("17.00")})
service, _ = Taxes.objects.get_or_create(
    name="service", defaults={"rate": Decimal("15.00")})

if Product.objects.count() == 0:
    Product.objects.create(
        name="Oil Filter", price_excl_tax=Decimal("800.00"), category=goods)
    Product.objects.create(
        name="Air Filter", price_excl_tax=Decimal("900.00"), category=goods)
    Product.objects.create(
        name="Brake Pads", price_excl_tax=Decimal("2500.00"), category=goods)
    Product.objects.create(name="Wheel Alignment",
                           price_excl_tax=Decimal("1200.00"), category=service)
    Product.objects.create(
        name="AC Service", price_excl_tax=Decimal("3500.00"), category=service)
    Product.objects.create(name="Engine Tuning",
                           price_excl_tax=Decimal("5000.00"), category=service)

customers = list(Customer.objects.all())
if not customers:
    for i in range(1, 11):
        c = Customer.objects.create(
            name=f"Customer {i}",
            address=f"Street {i}, Lahore",
            srtn=f"STRN-{i:04d}",
            ntn=f"NTN-{i:04d}",
        )
        Vehicle.objects.create(customer=c, make="Toyota",
                               number=f"LEA-{1000+i}")
        Vehicle.objects.create(customer=c, make="Honda",
                               number=f"LEB-{2000+i}")
    customers = list(Customer.objects.all())

for c in customers:
    if c.vehicles.count() == 0:
        Vehicle.objects.create(customer=c, make="Suzuki",
                               number=f"LEC-{random.randint(3000, 9999)}")

products = list(Product.objects.all())
vehicles_by_customer = {c.id: list(c.vehicles.all()) for c in customers}

created = 0
for _ in range(50):
    c = random.choice(customers)
    v = random.choice(vehicles_by_customer[c.id])
    inv = Invoice.objects.create(
        customer=c, vehicle=v, date=timezone.now(), status="unpaid")
    for _ in range(random.randint(1, 3)):
        p = random.choice(products)
        qty = random.randint(1, 5)
        InvoiceItem.objects.create(invoice=inv, product=p, qty=qty)
    inv.update_totals()
    created += 1

print(f"Created {created} invoices.")

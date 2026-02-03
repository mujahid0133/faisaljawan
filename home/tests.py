from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import Customer, Vehicle, Product, Taxes, Invoice, InvoiceItem


class CustomerModelTest(TestCase):
    def test_customer_creation(self):
        customer = Customer.objects.create(
            name="Test Customer",
            address="123 Test St",
            srtn="STRN-001",
            ntn="NTN-001"
        )
        self.assertEqual(customer.name, "Test Customer")
        self.assertEqual(str(customer), "Test Customer")


class VehicleModelTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Test Customer")

    def test_vehicle_creation(self):
        vehicle = Vehicle.objects.create(
            customer=self.customer,
            make="Toyota",
            number="ABC-123"
        )
        self.assertEqual(vehicle.make, "Toyota")
        self.assertEqual(str(vehicle), "Toyota (ABC-123)")


class TaxesModelTest(TestCase):
    def test_taxes_creation(self):
        tax = Taxes.objects.create(
            name="goods",
            rate=Decimal("17.00")
        )
        self.assertEqual(tax.name, "goods")
        self.assertEqual(tax.rate, Decimal("17.00"))


class ProductModelTest(TestCase):
    def setUp(self):
        self.tax = Taxes.objects.create(name="goods", rate=Decimal("17.00"))

    def test_product_creation(self):
        product = Product.objects.create(
            name="Oil Filter",
            price_excl_tax=Decimal("100.00"),
            category=self.tax
        )
        self.assertEqual(product.name, "Oil Filter")
        self.assertEqual(product.price_excl_tax, Decimal("100.00"))


class InvoiceModelTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Test Customer")
        self.vehicle = Vehicle.objects.create(
            customer=self.customer,
            make="Honda",
            number="XYZ-789"
        )

    def test_invoice_creation(self):
        invoice = Invoice.objects.create(
            customer=self.customer,
            vehicle=self.vehicle
        )
        self.assertTrue(invoice.invoice_no.startswith("MFES"))
        self.assertEqual(invoice.status, "unpaid")

    def test_invoice_auto_number(self):
        invoice1 = Invoice.objects.create(
            customer=self.customer,
            vehicle=self.vehicle
        )
        invoice2 = Invoice.objects.create(
            customer=self.customer,
            vehicle=self.vehicle
        )
        # Extract numbers from invoice_no
        num1 = int(invoice1.invoice_no.replace("MFES", ""))
        num2 = int(invoice2.invoice_no.replace("MFES", ""))
        self.assertEqual(num2, num1 + 1)


class InvoiceItemModelTest(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(name="Test Customer")
        self.vehicle = Vehicle.objects.create(
            customer=self.customer,
            make="Honda",
            number="XYZ-789"
        )
        self.tax = Taxes.objects.create(name="goods", rate=Decimal("17.00"))
        self.product = Product.objects.create(
            name="Test Product",
            price_excl_tax=Decimal("100.00"),
            category=self.tax
        )
        self.invoice = Invoice.objects.create(
            customer=self.customer,
            vehicle=self.vehicle
        )

    def test_invoice_item_calculations(self):
        item = InvoiceItem.objects.create(
            invoice=self.invoice,
            product=self.product,
            qty=2
        )
        # Tax amount should be (100 * 2) * 0.17 = 34.00
        self.assertEqual(item.tax_amount, Decimal("34.00"))
        # Total with tax should be 200 + 34 = 234.00
        self.assertEqual(item.price_incl_tax, Decimal("234.00"))

    def test_invoice_totals_update(self):
        InvoiceItem.objects.create(
            invoice=self.invoice,
            product=self.product,
            qty=2
        )
        self.invoice.refresh_from_db()
        self.assertEqual(self.invoice.total_excl_tax, Decimal("200.00"))
        self.assertEqual(self.invoice.total_tax, Decimal("34.00"))
        self.assertEqual(self.invoice.total_incl_tax, Decimal("234.00"))


class InvoiceViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = Customer.objects.create(name="Test Customer")
        self.vehicle = Vehicle.objects.create(
            customer=self.customer,
            make="Honda",
            number="XYZ-789"
        )
        self.tax = Taxes.objects.create(name="goods", rate=Decimal("17.00"))
        self.product = Product.objects.create(
            name="Test Product",
            price_excl_tax=Decimal("100.00"),
            category=self.tax
        )
        self.invoice = Invoice.objects.create(
            customer=self.customer,
            vehicle=self.vehicle
        )
        InvoiceItem.objects.create(
            invoice=self.invoice,
            product=self.product,
            qty=1
        )

    def test_bill_report_view(self):
        response = self.client.get('/billreport/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('invoices', response.context)
        self.assertIn('grand_total', response.context)

    def test_bill_report_with_ids(self):
        response = self.client.get(f'/billreport/?ids={self.invoice.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['invoices']), 1)

    def test_invoice_pdf_view(self):
        response = self.client.get(f'/invoice/{self.invoice.pk}/pdf/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('invoice', response.context)

    def test_invoice_pdf_goods_view(self):
        response = self.client.get(f'/invoice/{self.invoice.pk}/pdf/goods/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['special_case'], 'goods')

    def test_invoice_pdf_services_view(self):
        # Create service category and product
        service_tax = Taxes.objects.create(
            name="service", rate=Decimal("15.00"))
        service_product = Product.objects.create(
            name="Service Product",
            price_excl_tax=Decimal("50.00"),
            category=service_tax
        )
        InvoiceItem.objects.create(
            invoice=self.invoice,
            product=service_product,
            qty=1
        )
        response = self.client.get(f'/invoice/{self.invoice.pk}/pdf/services/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['special_case'], 'services')


class InvoiceFilteringTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = Customer.objects.create(name="Test Customer")
        self.vehicle = Vehicle.objects.create(
            customer=self.customer,
            make="Honda",
            number="XYZ-789"
        )
        self.goods_tax = Taxes.objects.create(
            name="goods", rate=Decimal("17.00"))
        self.service_tax = Taxes.objects.create(
            name="service", rate=Decimal("15.00"))

        self.goods_product = Product.objects.create(
            name="Goods Product",
            price_excl_tax=Decimal("100.00"),
            category=self.goods_tax
        )
        self.service_product = Product.objects.create(
            name="Service Product",
            price_excl_tax=Decimal("50.00"),
            category=self.service_tax
        )

        self.invoice = Invoice.objects.create(
            customer=self.customer,
            vehicle=self.vehicle
        )
        InvoiceItem.objects.create(
            invoice=self.invoice,
            product=self.goods_product,
            qty=1
        )
        InvoiceItem.objects.create(
            invoice=self.invoice,
            product=self.service_product,
            qty=1
        )

    def test_goods_filtering(self):
        response = self.client.get(f'/invoice/{self.invoice.pk}/pdf/goods/')
        items = response.context['items']
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].product.name, "Goods Product")

    def test_services_filtering(self):
        response = self.client.get(f'/invoice/{self.invoice.pk}/pdf/services/')
        items = response.context['items']
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].product.name, "Service Product")

    def test_has_goods_method(self):
        self.assertTrue(self.invoice.has_goods())

    def test_has_services_method(self):
        self.assertTrue(self.invoice.has_services())

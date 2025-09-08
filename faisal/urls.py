"""
URL configuration for faisal project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from home.views import invoice_pdf, invoice_pdf_goods, invoice_pdf_services, bill_report

urlpatterns = [
    path('admin/', admin.site.urls),
    path("invoice/<int:pk>/pdf/", invoice_pdf),
    path("invoice/<int:pk>/pdf/goods/",
         invoice_pdf_goods, name="invoice_pdf_goods"),
    path("invoice/<int:pk>/pdf/services/",
         invoice_pdf_services, name="invoice_pdf_services"),
    path("billreport/", bill_report, name="bill_report"),
]

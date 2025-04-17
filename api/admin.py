from django.contrib import admin

from api.models import Customer, Order


# Register your models here.
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'phone_number', 'date_created')
    search_fields = ('name', 'code', 'phone_number')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('customer', 'amount', 'status', 'date_created')
    search_fields = ('customer__name', 'status')
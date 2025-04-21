from django.contrib import admin

from api.models import Customer, Order, User


# Register your models here.
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'user', 'date_created')
    search_fields = ('name', 'code', 'phone_number')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('customer', 'amount', 'status', 'date_created')
    search_fields = ('customer__name', 'status')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('openid_user_id', 'name', 'email', 'role','phone_number')
    search_fields = ('openid_user_id', 'name', 'email', 'role')
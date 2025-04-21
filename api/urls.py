from django.urls import path, include

urlpatterns = [
    path('auth/', include('api.interfaces.authhandler'), name='authentication'),
    path('lookup/', include('api.interfaces.lookups'), name='lookup'),
    path('customers/', include('api.interfaces.handlecustomer'), name='customers'),
    path('orders/', include('api.interfaces.handleorders'), name='orders'),
]
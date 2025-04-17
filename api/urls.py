from django.urls import path, include

urlpatterns = [
    path('auth/', include('api.interfaces.authhandler'), name='authentication'),
    path('customers/', include('api.interfaces.handlecustomer'), name='customers'),
    path('orders/', include('api.interfaces.handleorders'), name='orders'),
]
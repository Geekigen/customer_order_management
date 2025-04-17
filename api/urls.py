from django.urls import path, include

urlpatterns = [
    path('auth/', include('api.interfaces.authhandler'), name='authentication'),
]
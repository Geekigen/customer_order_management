"""Base Services"""
from api.models import *
from customer_app.services.servicebase import ServiceBase


class CustomerService(ServiceBase):
	"""
	Service class for managing customers
	"""
	manager = Customer.objects

class OrderService(ServiceBase):
    """
    Service class for managing orders
    """
    manager = Order.objects
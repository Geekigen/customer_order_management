import uuid

from django.db import models

# Create your models here.
class BaseModel(models.Model):
    """
	Define repetitive methods to avoid cycles of redefining in every model.
	"""
    id = models.UUIDField(max_length=40, default=uuid.uuid4, unique=True, editable=False, primary_key=True)
    date_modified = models.DateTimeField(auto_now=True)
    date_created = models.DateTimeField(auto_now_add=True)
    synced = models.BooleanField(default=False)

    SYNC_MODEL = False

    objects = models.Manager()

    class Meta(object):
        """Meta"""
        abstract = True


class GenericBaseModel(BaseModel):
    """
	Define repetitive methods to avoid cycles of redefining in every model.
	"""
    name = models.CharField(max_length=200)
    description = models.TextField(max_length=255, blank=True, null=True)

    class Meta(object):
        """Meta"""
        abstract = True

class User(BaseModel):
    openid_user_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(null=True ,max_length=15, unique=True)
    role = models.CharField(max_length=20, choices=[('admin', 'Admin'), ('user', 'User')], default='user')
    def __str__(self):
        return self.name



# customers model
class Customer(GenericBaseModel):
    """
   The Customer model represents a customer in the system.
   it inherits from GenericBaseModel to include common fields like name and description.
    """

    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    code= models.TextField(blank=True, null=True)
    def __str__(self):
        return self.name

class Order(BaseModel):
    """
   The Order model represents an order placed by a customer.
   it inherits from BaseModel to include common fields like id, date_modified, and date_created.
    """

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    item = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('Pending', 'Pending'), ('Completed', 'Completed')])

    def __str__(self):
        return f"Order {self.id} - {self.customer.name}"

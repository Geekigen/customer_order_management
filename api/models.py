import uuid

from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models

# Create your models here.
from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('role', 'admin')
        return self.create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email):
        return self.get(email=email)
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

class User(BaseModel,AbstractBaseUser):
    openid_user_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(null=True ,max_length=15, unique=True, blank=True)
    password = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=20, choices=[('admin', 'Admin'), ('user', 'User')], default='user')
    def __str__(self):
        return self.name

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.name

    def has_perm(self, perm, obj=None):
        # Admin has all permissions
        return self.role == 'admin'

    def has_module_perms(self, app_label):
        # Admin has access to all modules
        return self.role == 'admin'

    @property
    def is_staff(self):
        # Admin users are staff
        return self.role == 'admin'



# customers model
class Customer(GenericBaseModel):
    """
   The Customer model represents a customer in the system.
   it inherits from GenericBaseModel to include common fields like name and description.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customers', null=True, blank=True)
    code= models.TextField(blank=True, null=True, unique=True)
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

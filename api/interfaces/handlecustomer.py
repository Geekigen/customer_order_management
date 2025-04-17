import json
import logging
import random
import string

from django.http import JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from api.interfaces.decorator import auth_required
from api.models import Customer

logger = logging.getLogger(__name__)

class CustomersManager:
    def _generate_customer_code(self):
        """
        Generate a unique customer code.
        The code consists of 8 uppercase letters and digits.
        """
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if Customer.objects.filter(code=code).exists():
            return self._generate_customer_code()
        return code

    @csrf_exempt
    @auth_required
    def create_customer(self, request):
        try:
            data = json.loads(request.body)
            name = data.get("name", "")
            phone_number = data.get("phone_number", "")
            email = data.get("email", "")
            code = self._generate_customer_code()
            if not name:
                return JsonResponse({"error": "Name is required"}, status=400)
            if not phone_number:
                return JsonResponse({"error": "Phone number is required"}, status=400)
            if not email:
                return JsonResponse({"error": "Email is required"}, status=400)
            if Customer.objects.filter(phone_number=phone_number).exists():
                return JsonResponse({"error": "Phone number already exists"}, status=400)
            if Customer.objects.filter(email=email).exists():
                return JsonResponse({"error": "Email already exists"}, status=400)
            customer = Customer.objects.create(
                name=name,
                phone_number=phone_number,
                email=email,
                code=code
            )
            return JsonResponse(
                {"message": "Customer created successfully", "customer_id": str(customer.id)}, status=201)
        except Exception as ex:
            logger.exception("Error creating customer: %s", ex)
            return JsonResponse({"error": str(ex)}, status=500)

    @csrf_exempt
    @auth_required
    def get_customer(self, request, customer_id):
        try:
            customer = Customer.objects.get(id=customer_id)
            customer_data = {
                "id": str(customer.id),
                "name": customer.name,
                "phone_number": customer.phone_number,
                "email": customer.email,
                "code": customer.code,
            }
            return JsonResponse(customer_data, status=200)
        except Customer.DoesNotExist:
            return JsonResponse({"error": "Customer not found"}, status=404)
        except Exception as ex:
            logger.exception("Error retrieving customer: %s", ex)
            return JsonResponse({"error": str(ex)}, status=500)

    @csrf_exempt
    @auth_required
    def update_customer(self, request, customer_id):
        try:
            data = json.loads(request.body)
            customer = Customer.objects.get(id=customer_id)
            customer.name = data.get("name", customer.name)
            customer.phone_number = data.get("phone_number", customer.phone_number)
            customer.email = data.get("email", customer.email)
            customer.save()
            return JsonResponse({"message": "Customer updated successfully"}, status=200)
        except Customer.DoesNotExist:
            return JsonResponse({"error": "Customer not found"}, status=404)
        except Exception as ex:
            logger.exception("Error updating customer: %s", ex)
            return JsonResponse({"error": str(ex)}, status=500)

    @csrf_exempt
    @auth_required
    def delete_customer(self, request, customer_id):
        try:
            customer = Customer.objects.get(id=customer_id)
            customer.delete()
            return JsonResponse({"message": "Customer deleted successfully"}, status=200)
        except Customer.DoesNotExist:
            return JsonResponse({"error": "Customer not found"}, status=404)
        except Exception as ex:
            logger.exception("Error deleting customer: %s", ex)
            return JsonResponse({"error": str(ex)}, status=500)


urlpatterns = [
    path('customer/create/', CustomersManager().create_customer, name='create_customer'),
    path('customer/<str:customer_id>/', CustomersManager().get_customer, name='get_customer'),
    path('customer/update/<str:customer_id>/', CustomersManager().update_customer, name='update_customer'),
    path('customer/delete/<str:customer_id>/', CustomersManager().delete_customer, name='delete_customer'),
]
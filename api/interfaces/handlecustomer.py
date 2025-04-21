import json
import logging
import random
import string

from django.http import JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from api.interfaces.decorator import auth_required
from api.interfaces.jwttokens import login_required
from api.models import *

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
    @login_required
    def create_customer(self, request):
        """
        Attempts to create a customer.
        @param request: The Django HTTP request received.
        @type request: HttpRequest
        """
        try:
            if request.method != "POST":
                return JsonResponse({"error": "Invalid request method, kindly use POST Request"}, status=405)
            data = json.loads(request.body)
            name = data.get("name", "")
            user_id = data.get("user_id", "")
            code = self._generate_customer_code()
            if not name:
                return JsonResponse({"error": "Name is required"}, status=400)
            if not user_id:
                return JsonResponse({"error": "User ID is required"}, status=400)
            user = User.objects.get(id=user_id)
            if not user:
                return JsonResponse({"error": "User not found"}, status=404)
            if not user.phone_number:
                return JsonResponse({"error": "User phone number is required kindly add phone number to the user "}, status=400)

            customer = Customer.objects.create(
                name=name,
                user = user,
                code=code
            )
            return JsonResponse(
                {"message": "Customer created successfully", "customer_id": str(customer.id),"customer_code":code}, status=201)
        except Exception as ex:
            logger.exception("Error creating customer: %s", ex)
            return JsonResponse({"error": str(ex)}, status=500)

customers_manager = CustomersManager()

urlpatterns = [
    path('create/', customers_manager.create_customer, name='create_customer')
]
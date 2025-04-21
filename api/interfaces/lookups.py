from django.core.paginator import Paginator
from django.http import JsonResponse
import logging

from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from api.interfaces.jwttokens import login_required
from api.models import User, Customer

logger = logging.getLogger(__name__)
class LookupManagement:
    """
    A class to manage user authentication and authorization using Auth0.
    It provides methods to create a user and verify a token.
    """

    @staticmethod
    @csrf_exempt
    @login_required
    def lookup_all_users(request):
        """
        Lookup all users in the database with pagination.
        """
        try:
            if request.method != "POST":
                return JsonResponse({"error": "Invalid request method, kindly use POST Request"}, status=405)
            page = int(request.GET.get("page", 1))
            per_page = int(request.GET.get("per_page", 10))
            users = User.objects.all()
            paginator = Paginator(users, per_page)
            paginated_users = paginator.get_page(page)
            return JsonResponse({
                "users": [
                    {
                        "id": str(user.id),
                        "email": user.email,
                        "name": user.name,
                        "role": user.role,
                        "phone_number": user.phone_number,
                    }
                    for user in paginated_users
                ],
                "page": page,
                "per_page": per_page,
                "total_pages": paginator.num_pages,
            }, status=200)
        except Exception as e:
            logger.error(f"Error fetching users: {e}")
            return JsonResponse({"error": f"Error fetching users: {e}"}, status=400)

    @staticmethod
    @csrf_exempt
    @login_required
    def lookup_customers(request):
        """
        Lookup all customers in the database with pagination.
        """
        try:
            if request.method != "POST":
                return JsonResponse({"error": "Invalid request method, kindly use POST Request"}, status=405)
            page = int(request.GET.get("page", 1))
            per_page = int(request.GET.get("per_page", 10))
            customers = Customer.objects.all()
            paginator = Paginator(customers, per_page)
            paginated_customers = paginator.get_page(page)
            return JsonResponse({
                "customers": [
                    {
                        "id": str(customer.id),
                        "email": customer.user.email,
                        "name": customer.user.name,
                        "phone_number": customer.user.phone_number,
                        "code": customer.code,
                    }
                    for customer in paginated_customers
                ],
                "page": page,
                "per_page": per_page,
                "total_pages": paginator.num_pages,
            }, status=200)
        except Exception as e:
            logger.error(f"Error fetching customers: {e}")
            return JsonResponse({"error": f"Error fetching customers: {e}"}, status=400)

urlpatterns = [
    path("all-users/", LookupManagement.lookup_all_users, name="lookup_all_users"),
    path("all-customers/", LookupManagement.lookup_customers, name="lookup_customers"),
]
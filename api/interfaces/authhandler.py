import json
import os

import requests
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.urls import path
from api.interfaces.oauth import verify_token
from django.views.decorators.csrf import csrf_exempt

from api.interfaces.validate_phonenumber import validate_phone_number
from customer_app import settings
from api.interfaces.jwttokens import generate_token, login_required
from api.models import User

AUTH0_DOMAIN = settings.AUTH0_DOMAIN
CLIENT_ID = settings.AUTH0_M2M_CLIENT_ID
CLIENT_SECRET = settings.AUTH0_M2M_CLIENT_SECRET
AUDIENCE = f"https://{AUTH0_DOMAIN}/api/v2/"


class UserManagement(object):
    """
    A class to manage user authentication and authorization using Auth0.
    It provides methods to create a user and verify a token.
    """

    def _save_user_to_db(self, user_data):
        """
        Save the user data to the database.
        """
        email = user_data.get("email", "")
        user_id = user_data.get("user_id", "")
        name = user_data.get("name", "")
        role = user_data.get("app_metadata", {}).get("role", "user")
        phone_number = user_data.get("app_metadata", {}).get("phone_number", "")
        password = user_data.get("app_metadata", {}).get("password", "")
        hashed_password = make_password(password)
        return User.objects.create(openid_user_id=user_id, email=email, name=name, role=role,phone_number=phone_number,password=hashed_password)




    def create_auth0_admin(self, email, password,phone_number):
        token = self.get_management_token()
        url = f"https://{AUTH0_DOMAIN}/api/v2/users"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "username": email.split("@")[0],
            "password": password,
            "email": email,
            "connection": "Username-Password-Authentication",
            "email_verified": True,
            "app_metadata": {"role": "admin","phone_number": phone_number,"password": password}
        }
        # print("PAYLOAD---------", payload,"token---------", token)
        try:
            res = requests.post(url, headers=headers, json=payload)
            res.raise_for_status()
        except Exception as err:
            print("HTTPError:", err)
        return res.json()

    @staticmethod
    def get_management_token():
        url = f"https://{AUTH0_DOMAIN}/oauth/token"
        payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "audience": AUDIENCE,
            "grant_type": "client_credentials"
        }
        res = requests.post(url, json=payload)
        res.raise_for_status()
        return res.json()["access_token"]

    @csrf_exempt
    def verify_token(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return JsonResponse({"error": "Authorization header missing"}, status=401)

        token = auth_header.split(" ")[1]

        try:
            user_info = verify_token(token)
            return JsonResponse({"message": "Authenticated", "user": user_info})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=401)

    @csrf_exempt
    def admin_register(self, request):
        """
        Authenticate a user the admin using Auth0.
        Expects a JSON payload with 'email' and 'password'.
        """
        try:
            if request.method != "POST":
                return JsonResponse({"error": "Invalid request method, kindly use POST Request"}, status=405)
            data = json.loads(request.body)
            email = data.get("email", "")
            password = data.get("password", "")
            api_key = data.get("api_key", "")
            phone_number = data.get("phone_number", "")
            if api_key != settings.ADMIN_API_KEY:
                return JsonResponse({"error": "Invalid API key"}, status=403)

            if not email:
                return JsonResponse({"error": "Email is required"}, status=400)
            if User.objects.filter(email=email).exists():
                return JsonResponse({"error": "Email already exists"}, status=400)
            if not phone_number:
                return JsonResponse({"error": "Phone number is required"}, status=400)
            if not validate_phone_number(phone_number):
                return JsonResponse({"error": "Invalid phone number make sure it starts with +2547"}, status=400)
            if phone_number and User.objects.filter(phone_number=phone_number).exists():
                return JsonResponse({"error": "Phone number already exists"}, status=400)

            if not password:
                return JsonResponse({"error": "Password is required"}, status=400)

            # Authenticate admin in Auth0
            admin_user = self.create_auth0_admin(email, password,phone_number)
            if admin_user.get("statusCode") == 401:
                return JsonResponse({"error": "Invalid credentials"}, status=401)

            if admin_user.get("statusCode") == 409:
                return JsonResponse({"error": "User already exists"}, status=409)
            # check if email is  "email_verified": true,
            if not admin_user.get("email_verified"):
                return JsonResponse({"error": "Email not verified"}, status=403)
            user = self._save_user_to_db(admin_user)
            token_data = generate_token(user)
            return JsonResponse({"message": "Admin created successfully",
                                 "user_id": str(user.id),"admin_details":admin_user,"Token":token_data}, status=201)

        except Exception as ex:
            return JsonResponse({"error": str(ex)}, status=500)


    @csrf_exempt
    def login(self, request):
        """
        Authenticate a user using Auth0.
        Expects a JSON payload with 'email' and 'password' and a valid api key.

        """
        try:
            if request.method != "POST":
                return JsonResponse({"error": "Invalid request method, kindly use POST Request"}, status=405)
            data = json.loads(request.body)
            email = data.get("email", "")
            password = data.get("password", "")
            if not email:
                return JsonResponse({"error": "Email is required"}, status=400)
            if not password:
                return JsonResponse({"error": "Password is required"}, status=400)

            # Authenticate user in Auth0
            user = authenticate(email=email, password=password)
            if not user:
                return JsonResponse({"error": "Invalid credentials"}, status=401)
            token = generate_token(user)

            return JsonResponse({"message": "Authenticated", "token": token}, status=200)

        except Exception as ex:
            return JsonResponse({"error": str(ex)}, status=500)

    @staticmethod
    @csrf_exempt
    @login_required
    def add_phone_number( request):
        """
        Add a phone number to the user's profile.
        Expects a JSON payload with 'phone_number'.
        """
        try:
            if request.method != "POST":
                return JsonResponse({"error": "Invalid request method, kindly use POST Request"}, status=405)
            data = json.loads(request.body)
            phone_number = data.get("phone_number", "")
            user_id = data.get("user_id", "")
            if not phone_number:
                return JsonResponse({"error": "Phone number is required"}, status=400)

            if not validate_phone_number(phone_number):
                return JsonResponse({"error": "Invalid phone number make sure it starts with +2547"}, status=400)
            if User.objects.filter(phone_number=phone_number).exists():
                return JsonResponse({"error": "Phone number already exists"}, status=400)
            if not user_id:
                return JsonResponse({"error": "User ID is required"}, status=400)
            user = User.objects.get(id=user_id)
            if not user:
                return JsonResponse({"error": "User not found"}, status=404)
            user.phone_number = phone_number
            user.save()
            return JsonResponse({"message": "Phone number added successfully"}, status=200)
        except Exception as ex:
            return JsonResponse({"error": str(ex)}, status=500)
urlpatterns = [
    path('admin-register/', UserManagement().admin_register, name='admin_register'),
    path('login/', UserManagement().login, name='login'),
    path('add-user-number/', UserManagement().add_phone_number, name='add_phone_number'),

]
import json
import os

import requests
from django.http import JsonResponse
from django.urls import path
from api.interfaces.oauth import verify_token
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

AUTH0_DOMAIN = settings.AUTH0_DOMAIN
CLIENT_ID = settings.AUTH0_M2M_CLIENT_ID
CLIENT_SECRET = settings.AUTH0_M2M_CLIENT_SECRET
AUDIENCE = f"https://{AUTH0_DOMAIN}/api/v2/"


class UserManagement:
    """
    A class to manage user authentication and authorization using Auth0.
    It provides methods to create a user and verify a token.
    """
    @csrf_exempt
    def create_user(self, request):
        """
        Create a user in Auth0.
        Expects a JSON payload with 'email' and 'password'.

        """
        try:
            data = json.loads(request.body)

            email = data.get("email", "")
            password = data.get("password", "")

            if not email:
                return JsonResponse({"error": "Email is required"}, status=400)

            if not password:
                return JsonResponse({"error": "Password is required"}, status=400)

            # Create user in Auth0
            user = self.create_auth0_user(email, password)
            """
            {"statusCode": 409, "error": "Conflict", "message": "The user already exists.", "errorCode": "auth0_idp_error"}}
            {"created_at": "2025-04-17T02:44:22.723Z", "email": "kipronokigen4@gmail.com", "email_verified": true, "identities": [{"connection": "Username-Password-Authentication", "user_id": "68006b06ce127a88b46349c6", "provider": "auth0", "isSocial": false}], "name": "kipronokigen4@gmail.com", "nickname": "kipronokigen4", "picture": "https://s.gravatar.com/avatar/efde4a529e208309a195c67eacf8726c?s=480&r=pg&d=https%3A%2F%2Fcdn.auth0.com%2Favatars%2Fki.png", "updated_at": "2025-04-17T02:44:22.723Z", "user_id": "auth0|68006b06ce127a88b46349c6", "app_metadata": {"role": "admin"}}}
            """

            print(user)
            return JsonResponse({"message": "User created successfully", "user": user}, status=201)

        except Exception as ex:
            return JsonResponse({"error": str(ex)}, status=500)


    def create_auth0_user(self, email, password):
        token = self.get_management_token()
        url = f"https://{AUTH0_DOMAIN}/api/v2/users"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "email": email,
            "password": password,
            "connection": "Username-Password-Authentication",
            "email_verified": True,
            "app_metadata": {"role": "admin"}
        }
        print("PAYLOAD---------", payload,"token---------", token)
        try:
            res = requests.post(url, headers=headers, json=payload)
            res.raise_for_status()
        except Exception as err:
            print("HTTPError:", err)
        # TODO: SAVE USER KWA DB ---- data iko kwa res.json()
        print("CREATE---------", res.json())
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





urlpatterns = [
    path('create-customer/', UserManagement().create_user, name='create_customer'),
]
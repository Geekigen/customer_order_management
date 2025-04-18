from functools import wraps
from django.http import JsonResponse
from api.interfaces.oauth import verify_token
from api.models import User
from django.utils.decorators import method_decorator
from django.views import View

def auth_required(view_func):
    @wraps(view_func)
    def _wrapped_view(self, request, *args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JsonResponse({"error": "Authorization header missing or invalid"}, status=401)

        token = auth_header.split(" ")[1]

        try:
            user_info = verify_token(token)
            user_id = user_info.get("sub")
            email = user_info.get("email")
            name = user_info.get("name", email.split('@')[0] if email else "Unknown")

            if not user_id or not email:
                return JsonResponse({"error": "Token payload missing required fields"}, status=400)

            # IF YOU WANT TO RESTRICT USER CREATION TO JUST API
            user = User.objects.filter(openid_user_id=user_id).first()
            if not user:
                return JsonResponse({"error": "User does not exist"}, status=403)

            # # Get or create the user ---- IF YOU WANT TO CREATE USER
            # user, created = User.objects.get_or_create(
            #     openid_user_id=user_id,
            #     defaults={"email": email, "name": name}
            # )

            # Attach user to request for downstream use
            request.user = user
            return view_func(self, request, *args, **kwargs)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=401)

    return _wrapped_view

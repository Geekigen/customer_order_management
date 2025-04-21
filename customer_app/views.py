import json
from authlib.integrations.django_client import OAuth
from customer_app import settings
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template import loader
from django.urls import reverse
from urllib.parse import quote_plus, urlencode
from api.models import User
import logging

logger = logging.getLogger(__name__)

oauth = OAuth()

oauth.register(
    "auth0",
    client_id=settings.AUTH0_FRONTEND_CLIENT_ID,
    client_secret=settings.AUTH0_FRONTEND_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{settings.AUTH0_DOMAIN}/.well-known/openid-configuration",
)

def login(request):
    return oauth.auth0.authorize_redirect(
        request, request.build_absolute_uri(reverse("callback"))
    )

def callback(request):
    token = oauth.auth0.authorize_access_token(request)
    logger.info("Access token retrieved successfully.")
    request.session["user"] = token

    # Save user to the database if not exists
    user_data = token.get("userinfo")
    email = user_data.get("email", "")
    user_id = user_data.get("sub", "")
    name = user_data.get("name", "")
    role = "user"

    if not User.objects.filter(email=email).exists():
        User.objects.create(
            openid_user_id=user_id,
            email=email,
            name=name,
            role=role,
        )
        logger.info(f"New user created: {email}")
    else:
        logger.info(f"User already exists in the database: {email}")

    return redirect(request.build_absolute_uri(reverse("index")))
def logout(request):
    request.session.clear()

    return redirect(
        f"https://{settings.AUTH0_DOMAIN}/v2/logout?"
        + urlencode(
            {
                "returnTo": request.build_absolute_uri(reverse("index")),
                "client_id": settings.AUTH0_FRONTEND_CLIENT_ID,
            },
            quote_via=quote_plus,
        ),
    )

def index(request):
    template = loader.get_template("index.html")
    context = {
        "session": request.session.get("user"),
        "pretty": json.dumps(request.session.get("user"), indent=4),
    }
    return HttpResponse(template.render(context, request))
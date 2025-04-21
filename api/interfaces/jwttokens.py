import jwt
from datetime import datetime, timedelta
import logging
from django.conf import settings
from django.http import JsonResponse
from django.core.cache import cache
from functools import wraps
import secrets

logger = logging.getLogger(__name__)

# JWT settings with better defaults
JWT_SECRET = getattr(settings, 'JWT_SECRET', None)
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET must be set in Django settings")

JWT_ALGORITHM = getattr(settings, 'JWT_ALGORITHM', 'HS256')
JWT_TOKEN_EXPIRATION = getattr(settings, 'JWT_TOKEN_EXPIRATION', 30 * 24 * 60)  # 30 days in minutes
JWT_AUDIENCE = getattr(settings, 'JWT_AUDIENCE', 'your-app-name')
JWT_ISSUER = getattr(settings, 'JWT_ISSUER', 'your-api-domain')
JWT_LEEWAY = getattr(settings, 'JWT_LEEWAY', 60)  # 60 seconds leeway for clock skew


class JWTError(Exception):
    """Base exception for JWT errors"""
    pass


class TokenExpiredError(JWTError):
    """Exception raised when token has expired"""
    pass


class InvalidTokenError(JWTError):
    """Exception raised when token is invalid"""
    pass


class BlacklistedTokenError(JWTError):
    """Exception raised when token has been blacklisted"""
    pass


def generate_token(user):
    """
    Generates a JWT token for the given user

    Args:
        user: Django user object

    Returns:
        dict: Dictionary containing token and expiration
    """
    iat = datetime.utcnow()
    jti = secrets.token_hex(16)  # JWT ID for token revocation

    payload = {
        'user_id': str(user.id),
        'username': user.name,
        'email': user.email,
        'is_staff': user.role == 'admin',
        'exp': iat + timedelta(minutes=JWT_TOKEN_EXPIRATION),
        'iat': iat,
        'iss': JWT_ISSUER,
        'aud': JWT_AUDIENCE,
        'jti': jti
    }

    return {
        'token': jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM),
        'expires_in': JWT_TOKEN_EXPIRATION * 60  # in seconds
    }


def decode_token(token):
    """
    Decodes and verifies a JWT token

    Args:
        token (str): The JWT token

    Returns:
        dict: The decoded payload

    Raises:
        TokenExpiredError: If token has expired
        InvalidTokenError: If token is invalid
        BlacklistedTokenError: If token has been blacklisted
    """
    try:
        # Check if token is blacklisted
        if is_token_blacklisted(token):
            raise BlacklistedTokenError("Token has been revoked")

        # Verify and decode the token
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM],
            options={
                'verify_signature': True,
                'verify_exp': True,
                'verify_iat': True,
                'verify_aud': True if JWT_AUDIENCE else False,
                'verify_iss': True if JWT_ISSUER else False,
                'require': ['exp', 'iat', 'user_id']
            },
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            leeway=JWT_LEEWAY
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.info("Token has expired")
        raise TokenExpiredError("Token has expired")
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise InvalidTokenError(f"Invalid token: {str(e)}")


def is_token_blacklisted(token):
    """
    Checks if a token has been blacklisted/revoked

    Args:
        token (str): The JWT token

    Returns:
        bool: True if token is blacklisted, False otherwise
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        jti = payload.get('jti')
        if jti and cache.get(f"blacklisted_token:{jti}"):
            return True
    except Exception as e:
        logger.warning(f"Error checking blacklist: {str(e)}")

    return False


def blacklist_token(token):
    """
    Blacklists a token so it can no longer be used
    Forces immediate expiration regardless of the token's original expiry

    Args:
        token (str): The JWT token to blacklist
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        jti = payload.get('jti')

        if jti:
            now = datetime.utcnow().timestamp()
            exp = payload.get('exp', now + 86400)
            ttl = max(1, int(exp - now))

            cache.set(f"blacklisted_token:{jti}", True, timeout=ttl)
            logger.info(f"Token {jti[:8]}... blacklisted")
    except Exception as e:
        logger.warning(f"Error blacklisting token: {str(e)}")


def get_token_from_request(request):
    """
    Extracts JWT token from various sources in the request

    Args:
        request: Django request object

    Returns:
        str: The token or None if not found
    """
    # First check Authorization header
    auth_header = request.headers.get('Authorization', '')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header.split(' ')[1]


    token = request.GET.get('token')
    if token:
        return token

    return None



def login_required(view_func=None, *, required=True, verify_staff=False):
    """
    Decorator to validate JWT token in protected views.
    Works with both regular functions and instance methods.

    Args:
        view_func: The view function to decorate
        required: If True, the token is required; if False, the view still works without token
        verify_staff: If True, requires the user to have staff permissions

    Returns:
        function: Decorated view function
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            # Determine if this is an instance method or regular function
            # For instance methods, first arg is 'self', second is request
            # For regular functions, first arg is request
            if args and hasattr(args[0], 'method'):
                # Regular function case - first arg is request
                request = args[0]
                view_args = args[1:]
            elif len(args) >= 2 and hasattr(args[1], 'method'):
                # Instance method case - first arg is self, second is request
                self_obj = args[0]
                request = args[1]
                view_args = args[2:]
            else:
                logger.error("No valid request object found in arguments")
                return JsonResponse({'error': 'Invalid request'}, status=400)

            # Handle preflight OPTIONS requests
            if request.method == 'OPTIONS':
                if len(args) >= 2 and hasattr(args[1], 'method'):
                    # Instance method case
                    return view_func(args[0], request, *view_args, **kwargs)
                else:
                    # Regular function case
                    return view_func(request, *view_args, **kwargs)

            # Get and validate token
            token = get_token_from_request(request)

            if not token:
                if required:
                    return JsonResponse({'error': 'Authentication required'}, status=401)
                else:
                    if len(args) >= 2 and hasattr(args[1], 'method'):
                        return view_func(args[0], request, *view_args, **kwargs)
                    else:
                        return view_func(request, *view_args, **kwargs)

            try:
                payload = decode_token(token)
                if verify_staff and not payload.get('is_staff', False):
                    return JsonResponse({'error': 'Staff privileges required'}, status=403)

                # Add authentication info to request
                request.user_id = payload['user_id']
                request.username = payload.get('username', '')
                request.is_authenticated = True
                request.token_payload = payload  # Store full payload

                # Call the view function with the right arguments
                if len(args) >= 2 and hasattr(args[1], 'method'):
                    # Instance method case
                    return view_func(args[0], request, *view_args, **kwargs)
                else:
                    # Regular function case
                    return view_func(request, *view_args, **kwargs)

            except TokenExpiredError:
                return JsonResponse({
                    'error': 'Token has expired',
                    'code': 'token_expired'
                }, status=401)

            except BlacklistedTokenError:
                return JsonResponse({
                    'error': 'Token has been revoked',
                    'code': 'token_revoked'
                }, status=401)

            except InvalidTokenError as e:
                return JsonResponse({
                    'error': str(e),
                    'code': 'invalid_token'
                }, status=401)

            except Exception as e:
                logger.error(f"Unexpected error in jwt_required: {str(e)}")
                return JsonResponse({'error': 'Authentication error'}, status=401)

        return wrapper

    if view_func is None:
        return decorator
    return decorator(view_func)




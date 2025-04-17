import os
import requests
from jose import jwt
from jose.exceptions import JWTError

AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE")
ALGORITHMS = ["RS256"]

def get_jwk():
    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    response = requests.get(jwks_url)
    response.raise_for_status()
    return response.json()

def verify_token(token: str):
    try:
        jwks = get_jwk()
        unverified_header = jwt.get_unverified_header(token)

        print(unverified_header)

        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
                break

        if not rsa_key:
            raise Exception("RSA key not found.")


        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer=f"https://{AUTH0_DOMAIN}/"
        )
        return payload

    except JWTError as e:
        raise Exception(f"Token is invalid: {str(e)}")

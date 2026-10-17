import jwt
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

ISSUER = "https://idp.exam.local"
AUDIENCE = "tds-2gehfmbr.apps.exam.local"

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA2okOHspNjgA+2rTLbeuY
cxiP/hG8C6Sb9iwg3yiLAA4HCnpITcbWCSelbvbYGuc3EbNy4xFyf5Cbj5DHJMID
EkryOgyd2giIIIBOUBj8S63uGcnRpOBh9NFatfNwheKuzsPuVNldu6A9cNteNpXc
WyJjG2axVfmq7i6SuKr1JoWYG7xTTAvKPujSl4OtsQfO3h5NepzdfXpr28oNnzfW
ed+zclR6BcmNNo/WVfJ4xyCLSf0BCOgdTgW6PdaChd1l9VDetJZVEgC5tkyvXsfI
SI6iyrYbKR0NEBSqq4XkadEjsCs4F1RncsS4LlgniT7GlkL9Mce3b0wGLs9/7ZIX
dQIDAQAB
-----END PUBLIC KEY-----"""

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

INVALID = {"valid": False}


class VerifyRequest(BaseModel):
    token: str


# If the body is missing or malformed, still answer {"valid": false}
@app.exception_handler(RequestValidationError)
async def bad_request(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=401, content=INVALID)


@app.post("/verify")
def verify(req: VerifyRequest):
    try:
        claims = jwt.decode(
            req.token,
            PUBLIC_KEY,
            algorithms=["RS256"],       # only accept RS256
            audience=AUDIENCE,          # checks aud
            issuer=ISSUER,              # checks iss
            options={"require": ["exp", "iss", "aud"]},  # these must exist; exp is checked automatically
        )
    except jwt.PyJWTError:
        # covers bad signature, expired, wrong aud/iss, garbage token, etc.
        return JSONResponse(status_code=401, content=INVALID)

    return {
        "valid": True,
        "email": claims.get("email"),
        "sub": claims.get("sub"),
        "aud": AUDIENCE,
    }
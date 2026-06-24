import json
import logging
from datetime import datetime, timezone

import requests

RESPONSE_LOG_LIMIT = 2000

API_KEY = "cAyzERqthCJXYVExjNAhr9CzE8ncLN2cQK3WGK10"
COGNITO_URL = "https://cognito-idp.eu-west-1.amazonaws.com/"
COGNITO_CLIENT_ID = "57ddq2ppqg2jcpup06r2g1deur"


class AuthError(Exception):
    pass


class PerfectDraftAPI:
    BASE_URL = "https://api.perfectdraft.com"

    def __init__(self, email, password, recorder=None, auth_log_path=None):
        self.email = email
        self.password = password
        self.access_token = None
        self.id_token = None
        self.refresh_token = None
        self.recorder = recorder
        self.auth_logger = self._build_auth_logger(auth_log_path) if auth_log_path else None

    @staticmethod
    def _build_auth_logger(path):
        logger = logging.getLogger(f"perfectdraft_auth.{id(path)}")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        if not logger.handlers:
            handler = logging.FileHandler(path, encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(handler)
        return logger

    @staticmethod
    def _redact_tokens(value):
        """Recursively truncates known token/secret fields so the log file
        never holds a full credential usable to sign in or impersonate."""
        sensitive_keys = {
            "password",
            "recaptchaToken",
            "REFRESH_TOKEN",
            "AccessToken",
            "IdToken",
            "RefreshToken",
        }
        if isinstance(value, dict):
            redacted = {}
            for k, v in value.items():
                if k in sensitive_keys and isinstance(v, str):
                    redacted[k] = f"{v[:12]}...redacted...({len(v)} chars)"
                else:
                    redacted[k] = PerfectDraftAPI._redact_tokens(v)
            return redacted
        if isinstance(value, list):
            return [PerfectDraftAPI._redact_tokens(v) for v in value]
        return value

    def _log_auth_event(self, event, request_payload, response):
        if not self.auth_logger:
            return
        safe_request = self._redact_tokens(request_payload)
        try:
            safe_response = self._redact_tokens(json.loads(response.text))
        except ValueError:
            safe_response = response.text[:RESPONSE_LOG_LIMIT]
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "request": safe_request,
            "status_code": response.status_code,
            "response": safe_response,
        }
        self.auth_logger.info(json.dumps(entry))

    def _record(self, method, url, response):
        if not self.recorder:
            return
        body = response.text[:RESPONSE_LOG_LIMIT]
        self.recorder(method, url, response.status_code, body)

    def load_tokens(self, access_token, id_token, refresh_token):
        self.access_token = access_token
        self.id_token = id_token
        self.refresh_token = refresh_token

    def authenticate(self, recaptcha_token):
        """One-time sign-in using a manually captured reCAPTCHA token (see
        GETTING_RECAPTCHA_TOKEN.md). After this, refresh_tokens() can renew
        the AccessToken/IdToken via Cognito without needing reCAPTCHA again."""
        url = f"{self.BASE_URL}/authentication/sign-in"
        headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
        payload = {
            "email": self.email,
            "password": self.password,
            "recaptchaToken": recaptcha_token,
            "recaptchaAction": "Magento/login",
        }
        response = requests.post(url, json=payload, headers=headers, timeout=15)
        self._record("POST", url, response)
        self._log_auth_event("authenticate", payload, response)
        if response.status_code != 200:
            raise AuthError(f"Authentication failed: {response.status_code} {response.text}")
        data = response.json()
        self.access_token = data.get("AccessToken")
        self.id_token = data.get("IdToken")
        self.refresh_token = data.get("RefreshToken")
        return self.access_token, self.id_token, self.refresh_token

    def refresh_tokens(self):
        """Renews AccessToken/IdToken using the cached RefreshToken, directly
        against AWS Cognito. No reCAPTCHA needed for this."""
        if not self.refresh_token:
            raise AuthError("No refresh token available")
        headers = {
            "Content-Type": "application/x-amz-json-1.1",
            "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
        }
        payload = {
            "AuthFlow": "REFRESH_TOKEN_AUTH",
            "ClientId": COGNITO_CLIENT_ID,
            "AuthParameters": {"REFRESH_TOKEN": self.refresh_token},
        }
        response = requests.post(COGNITO_URL, json=payload, headers=headers, timeout=15)
        self._record("POST", COGNITO_URL, response)
        self._log_auth_event("refresh_tokens", payload, response)
        if response.status_code != 200:
            raise AuthError(f"Token refresh failed: {response.status_code} {response.text}")
        result = response.json().get("AuthenticationResult", {})
        self.access_token = result.get("AccessToken")
        self.id_token = result.get("IdToken")
        return self.access_token, self.id_token, self.refresh_token

    def _auth_headers(self):
        # The api.perfectdraft.com backend expects the Cognito AccessToken
        # in a custom x-access-token header, not a standard Authorization
        # Bearer header (confirmed by live testing against /api/me).
        return {"x-access-token": self.access_token}

    def get_user_info(self):
        url = f"{self.BASE_URL}/api/me"
        response = requests.get(url, headers=self._auth_headers(), timeout=15)
        self._record("GET", url, response)
        if response.status_code == 401:
            raise AuthError("Access token rejected (401)")
        response.raise_for_status()
        return response.json()

    def get_machine_info(self, machine_id):
        url = f"{self.BASE_URL}/api/perfectdraft_machines/{machine_id}"
        response = requests.get(url, headers=self._auth_headers(), timeout=15)
        self._record("GET", url, response)
        if response.status_code == 401:
            raise AuthError("Access token rejected (401)")
        response.raise_for_status()
        return response.json()

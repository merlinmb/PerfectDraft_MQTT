import json
import os


class TokenStore:
    """Persists PerfectDraft auth tokens to disk so re-authentication
    (which requires a manually captured reCAPTCHA token) isn't needed
    on every run."""

    def __init__(self, path):
        self.path = path

    def load(self):
        if not os.path.exists(self.path):
            return None
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, access_token, id_token, refresh_token):
        data = {
            "AccessToken": access_token,
            "IdToken": id_token,
            "RefreshToken": refresh_token,
        }
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f)

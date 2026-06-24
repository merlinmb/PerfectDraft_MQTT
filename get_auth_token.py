"""Authenticate against the PerfectDraft API from your local machine
(outside Docker) using a manually captured reCAPTCHA token, and save the
resulting tokens to ./data/token_cache.json.

Usage:
    python get_auth_token.py "<recaptcha_token>"

After running, copy data/token_cache.json to the Pi's data folder
(/home/pi/portainer_data/perfectdraft/token_cache.json) so the running
container picks it up without needing --auth-token inside the container.
"""
import argparse
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent / "src"))

from perfectdraft_api import AuthError, PerfectDraftAPI  # noqa: E402
from token_store import TokenStore  # noqa: E402

CONFIG_PATH = Path(__file__).parent / "config.yaml"
TOKEN_PATH = Path(__file__).parent / "data" / "token_cache.json"
AUTH_LOG_PATH = Path(__file__).parent / "data" / "auth.log"


def main():
    parser = argparse.ArgumentParser(description="Authenticate to PerfectDraft and cache tokens locally")
    parser.add_argument("recaptcha_token", help="Manually captured reCAPTCHA token")
    args = parser.parse_args()

    if not CONFIG_PATH.exists():
        print(f"Config file not found: {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    AUTH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    pd_cfg = config["perfectdraft"]
    api = PerfectDraftAPI(pd_cfg["email"], pd_cfg["password"], auth_log_path=str(AUTH_LOG_PATH))

    try:
        access_token, id_token, refresh_token = api.authenticate(args.recaptcha_token)
    except AuthError as e:
        print(f"Authentication failed: {e}", file=sys.stderr)
        sys.exit(1)

    token_store = TokenStore(str(TOKEN_PATH))
    token_store.save(access_token, id_token, refresh_token)

    print(f"Authentication successful. Tokens saved to {TOKEN_PATH}")
    print("Copy this file to the Pi to make it available to the running container:")
    print(f'  scp "{TOKEN_PATH}" pi@homebridge.local:/home/pi/portainer_data/perfectdraft/token_cache.json')


if __name__ == "__main__":
    main()

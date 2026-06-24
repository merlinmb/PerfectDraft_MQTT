import argparse
import logging
import sys
import threading
import time

import requests
import yaml

from history_store import history_store
from mqtt_publisher import MqttPublisher
from perfectdraft_api import AuthError, PerfectDraftAPI
from state import state
from token_store import TokenStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("perfectdraft_mqtt")

CONFIG_PATH = "/data/config.yaml"
TOKEN_PATH = "/data/token_cache.json"
AUTH_LOG_PATH = "/data/auth.log"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_api(config, token_store):
    pd_cfg = config["perfectdraft"]
    api = PerfectDraftAPI(
        pd_cfg["email"], pd_cfg["password"], recorder=state.record_call, auth_log_path=AUTH_LOG_PATH
    )
    tokens = token_store.load()
    if tokens:
        api.load_tokens(tokens.get("AccessToken"), tokens.get("IdToken"), tokens.get("RefreshToken"))
        state.set_auth_status(True)
    return api


def start_web_server(port):
    from web import app

    threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False),
        daemon=True,
    ).start()
    log.info("Admin web UI listening on port %s", port)


def discover_machine_id(user_info):
    machines = user_info.get("perfectdraftMachines")
    if machines:
        first = machines[0]
        if isinstance(first, dict):
            for id_key in ("id", "machine_id", "serial_number"):
                if id_key in first:
                    return first[id_key]
        else:
            return first
    raise RuntimeError(
        "Could not auto-discover machine_id from perfectdraftMachines in /api/me response. "
        "Set perfectdraft.machine_id explicitly in config.yaml."
    )


def run_auth(args):
    config = load_config()
    token_store = TokenStore(TOKEN_PATH)
    api = build_api(config, token_store)
    try:
        access_token, id_token, refresh_token = api.authenticate(args.recaptcha_token)
    except AuthError as e:
        state.set_auth_status(False, error=str(e))
        raise
    token_store.save(access_token, id_token, refresh_token)
    state.set_auth_status(True)
    log.info("Authentication successful, tokens saved to %s", TOKEN_PATH)


def call_with_refresh(api, token_store, func, *args):
    """Calls func(*args) on the api; on a 401 AuthError, tries a Cognito
    token refresh (no reCAPTCHA needed) once before re-raising."""
    refreshed = False
    transient_attempts = 0
    max_transient_attempts = 3

    while True:
        try:
            return func(*args)
        except AuthError:
            if refreshed:
                raise
            log.info("Access token expired, attempting refresh via Cognito")
            access_token, id_token, refresh_token = api.refresh_tokens()
            token_store.save(access_token, id_token, refresh_token)
            state.set_auth_status(True)
            refreshed = True
        except requests.exceptions.RequestException as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code is not None and status_code < 500 and status_code != 429:
                raise

            transient_attempts += 1
            if transient_attempts >= max_transient_attempts:
                raise

            log.warning(
                "Transient API error calling %s (attempt %s/%s): %s",
                func.__name__,
                transient_attempts,
                max_transient_attempts,
                exc,
            )
            time.sleep(2)


def run_loop():
    config = load_config()
    token_store = TokenStore(TOKEN_PATH)
    api = build_api(config, token_store)

    web_cfg = config.get("web", {})
    if web_cfg.get("enabled", True):
        start_web_server(web_cfg.get("port", 8080))

    if not api.access_token:
        log.error(
            "No cached auth tokens found. Run with --auth-token <recaptcha_token> "
            "once to authenticate before starting the polling loop."
        )
        sys.exit(1)

    mqtt_cfg = config["mqtt"]
    publisher = MqttPublisher(
        mqtt_cfg["host"],
        mqtt_cfg.get("port", 1883),
        mqtt_cfg.get("username") or None,
        mqtt_cfg.get("password") or None,
        mqtt_cfg.get("base_topic", "perfectdraft"),
    )

    machine_id = config["perfectdraft"].get("machine_id")
    poll_interval = config["perfectdraft"].get("poll_interval_seconds", 60)

    while True:
        try:
            if not machine_id:
                user_info = call_with_refresh(api, token_store, api.get_user_info)
                machine_id = discover_machine_id(user_info)
                state.set_machine_id(machine_id)
                log.info("Discovered machine_id: %s", machine_id)

            machine_info = call_with_refresh(api, token_store, api.get_machine_info, machine_id)
            publisher.publish_machine_state(machine_id, machine_info)
            history_store.record_machine_sample(machine_id, machine_info)
            state.set_machine_info(machine_info)
            state.set_poll_status()
            log.info("Published machine state for %s", machine_id)
        except AuthError as e:
            state.set_auth_status(False, error=str(e))
            state.set_poll_status(error=str(e))
            log.error("%s", e)
            log.error("Refresh token also rejected — re-run with --auth-token <recaptcha_token>.")
        except Exception as e:
            state.set_poll_status(error=str(e))
            log.exception("Error during poll cycle")

        time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(description="PerfectDraft -> MQTT bridge")
    parser.add_argument(
        "--auth-token",
        dest="recaptcha_token",
        help="Manually captured reCAPTCHA token, used once to authenticate and cache tokens",
    )
    args = parser.parse_args()

    if args.recaptcha_token:
        run_auth(args)
        return

    run_loop()


if __name__ == "__main__":
    main()

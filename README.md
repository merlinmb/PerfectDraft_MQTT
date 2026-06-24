# PerfectDraft MQTT Bridge

Polls the PerfectDraft cloud API for machine state and publishes it to a local MQTT broker.

## Setup

1. Copy `config.example.yaml` to `config.yaml` and fill in your PerfectDraft email/password and MQTT broker settings. `config.yaml` is the file the container reads at `/data/config.yaml`.
2. The PerfectDraft API requires a Google reCAPTCHA Enterprise token for the *initial* sign-in. Generate one from your browser's console — see [GETTING_RECAPTCHA_TOKEN.md](GETTING_RECAPTCHA_TOKEN.md) — then authenticate once, either with [get_auth_token.py](get_auth_token.py) outside Docker, or:

   ```
   docker compose run --rm perfectdraft-mqtt python main.py --auth-token "<captured_token>"
   ```

   This saves `AccessToken`/`IdToken`/`RefreshToken` to `token_cache.json` in the data folder.

3. Start the polling loop:

   ```
   docker compose up -d
   ```

After the initial sign-in, the bridge automatically refreshes its `AccessToken`/`IdToken` via AWS Cognito using the long-lived `RefreshToken` (~30 days) — no reCAPTCHA needed for that. You'll only need to repeat step 2 if the refresh token itself expires or is revoked.

## Machine ID

The bridge auto-discovers your machine ID from the `perfectdraftMachines` array in `/api/me`. If that fails, set `perfectdraft.machine_id` explicitly in `config.yaml`.

## Deploying to homebridge.local

```
./deploy.sh
```

Copies the project to `/home/pi/portainer_data/perfectdraft/` on `homebridge.local` via scp. First-time setup still requires creating `config.yaml` on the Pi and running the `--auth-token` step there (see Setup above), then `docker compose up -d --build`.

## MQTT Topic

State is published (retained) to `<base_topic>/<machine_id>/state` as JSON.

## Admin Web UI

A small status page is served on port `8080` (configurable via `web.port` in `config.yaml`, or disable with `web.enabled: false`). It shows:

- Current authentication status, last successful auth time, and last auth error
- Discovered machine ID
- Last poll time/error
- A rolling log of the most recent API calls (method, URL, status code, response body)

Visit `http://<host>:8080/` — it auto-refreshes every 10 seconds.

## Auth Log

Every `authenticate()` and `refresh_tokens()` call is written to `auth.log` in the data folder (`/data/auth.log` in the container, `data/auth.log` next to `get_auth_token.py` when run locally) as one JSON line per event: timestamp, request payload, status code, and response body. Passwords and token values are truncated/redacted before being written, so the log is safe to inspect even though it captures full request/response detail for debugging auth issues.

## Sensitive Files and .gitignore

For security, sensitive files like `config.yaml` (which contains API credentials) and `data/token_cache.json` (authentication tokens) are excluded from version control using `.gitignore`. The `.gitignore` file also excludes Python bytecode files (`__pycache__/`, `*.pyc`) and the entire `data/` directory to keep the repository clean. Please ensure these files remain excluded when contributing.

## GitHub Upload Preparation

Before pushing to GitHub, verify your local repository is initialized and ignore rules are active:

1. Initialize Git (if needed):

   ```
   git init
   git remote add origin https://github.com/merlinmb/PerfectDraft_MQTT
   ```

2. Confirm sensitive files are ignored:

   ```
   git check-ignore -v config.yaml data/token_cache.json data/auth.log
   ```

3. Review what will be committed:

   ```
   git status --short
   ```

Only commit non-sensitive project files.

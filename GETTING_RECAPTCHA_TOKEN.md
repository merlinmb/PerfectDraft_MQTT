# How to Get a reCAPTCHA Token for PerfectDraft Login

PerfectDraft's website uses Google reCAPTCHA Enterprise, which can't be solved headlessly. Instead, generate a token directly in your browser's console — this is the same token the site itself generates internally before signing you in.

## Steps

1. Go to `https://www.perfectdraft.com/en-gb/customer/account/login` in your browser.
2. Open the developer console: `F12` → **Console** tab (Chrome/Edge/Firefox all have one).
3. Paste this command and press Enter:

   ```javascript
   grecaptcha.enterprise.execute('6LcZQiUoAAAAAAO3JUjLiT470c-pNXbWyepuvMtV', {action: 'Magento/login'}).then(t => console.log(t))
   ```

4. A long token string will be printed to the console a moment later. Copy it (right-click → Copy, or select the text and `Ctrl+C`).
ls
> **Tips**
> - You do **not** need to log in on that page; just open it and let it finish loading.
> - The value you need is the long string the command prints (about 2,500 characters), **not** the site key `6LcZQi...` that appears inside the command.
> - Line wraps in the console are only visual. To check the token is clean, run `console.log('[' + tok + ']')` after storing it with `.then(t => { window.tok = t })`; the token is everything between `[` and `]`. The scripts also strip stray whitespace and quotes.
> - The token expires within about 2 minutes and works once, so use it immediately.

## Using the token

The token is time-limited, so use it right away. On the machine that runs the bridge (e.g. the Pi), from the project folder (the one containing `docker-compose.yml`):

```
cd /home/pi/portainer_data/perfectdraft
docker compose build
docker compose run --rm perfectdraft-mqtt python main.py --auth-token "<paste_token_here>"
docker compose up -d
```

`build` makes sure the container has the latest code, `run` authenticates and saves the tokens to `token_cache.json` in the data folder, and `up -d` starts (or restarts) the polling loop.

If you see "Authentication failed", the token expired before you used it — just re-run the console command for a fresh one.

If you still see `PreAuthentication failed with error 'domain'`, the container is running old code: copy the updated `src/` to the Pi (`./deploy.sh`) and run `docker compose build` again.

## How sign-in works

Sign-in goes directly to AWS Cognito (`InitiateAuth`, `USER_PASSWORD_AUTH`), passing the reCAPTCHA token, the action `Magento/login` and `domain: https://www.perfectdraft.com` in `ClientMetadata`. PerfectDraft's pre-authentication Lambda rejects sign-in with `'domain'` if that field is missing. The older `api.perfectdraft.com/authentication/sign-in` gateway doesn't forward it, so it can't be used.

## Related project

The Home Assistant integration [brettjenkins/hassio-integration-perfectdraft-pro](https://github.com/brettjenkins/hassio-integration-perfectdraft-pro) uses the same flow and appears to be actively maintained. Check it if PerfectDraft changes their login again.

## After the first login

You won't need to repeat this often. Once authenticated, the bridge automatically refreshes its `AccessToken`/`IdToken` using the long-lived `RefreshToken` (valid ~30 days) via AWS Cognito — no reCAPTCHA required for that. You'll only need to repeat this guide if the refresh token itself expires or is revoked.

## Notes

- Don't share this token with anyone — while short-lived, it can be used to sign in to your account.
- If `grecaptcha` is undefined in the console, make sure you're on the actual login page (`/customer/account/login`) and that the page has fully loaded.

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

## Using the token

The token is time-limited, so use it right away — either:

**Outside Docker (recommended for getting started):**
```
python get_auth_token.py "<paste_token_here>"
```
This reads `config.yaml` in the project root, authenticates, and saves the tokens to `data/token_cache.json` (then tells you the `scp` command to push it to the Pi).

**Inside the running container:**
```
docker compose run --rm perfectdraft-mqtt python main.py --auth-token "<paste_token_here>"
```

If you see "Authentication failed", the token expired before you used it — just re-run the console command for a fresh one.

## After the first login

You won't need to repeat this often. Once authenticated, the bridge automatically refreshes its `AccessToken`/`IdToken` using the long-lived `RefreshToken` (valid ~30 days) via AWS Cognito — no reCAPTCHA required for that. You'll only need to repeat this guide if the refresh token itself expires or is revoked.

## Notes

- Don't share this token with anyone — while short-lived, it can be used to sign in to your account.
- If `grecaptcha` is undefined in the console, make sure you're on the actual login page (`/customer/account/login`) and that the page has fully loaded.

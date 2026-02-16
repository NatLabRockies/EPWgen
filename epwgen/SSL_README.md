Diagnosing SSL / corporate proxy issues and configuring EPWgen

Quick diagnostics (macOS / zsh)
- Check relevant environment variables (HTTP(S) proxies and our new EPWgen vars):

```bash
# Print proxy and EPWgen-related env vars
env | egrep -i "(proxy|http_proxy|https_proxy|EPWGEN_CA_BUNDLE|EPWGEN_VERIFY)"
```

- Use curl to test TLS handshake and show which certificate chain is presented by the server (helpful to detect SSL inspection):

```bash
# Do a verbose TLS connection to the NASA POWER API
curl -vI --silent "https://power.larc.nasa.gov/api/temporal/hourly/point?community=SB&parameters=&longitude=-84.6667&latitude=39.05&start=20240101&end=20241231&format=EPW" 2>&1 | sed -n '1,120p'

# Show the server certificate chain (useful when corporate MITM rewrites certs)
echo | openssl s_client -showcerts -servername power.larc.nasa.gov -connect power.larc.nasa.gov:443 2>/dev/null | sed -n '1,200p'
```

- Test requests with Python against the same endpoint (shows SSL errors from requests/certifi):

```bash
python - <<'PY'
import requests
from epwgen.ssl_utils import get_verify_arg
url = 'https://power.larc.nasa.gov/api/temporal/hourly/point?community=SB&parameters=&longitude=-84.6667&latitude=39.05&start=20240101&end=20241231&format=EPW'
try:
    r = requests.get(url, timeout=10, verify=get_verify_arg())
    print('HTTP', r.status_code)
except Exception as e:
    print('ERROR', e)
PY
```

When you see a certificate signed by your company's CA (or a mismatch), you'll need to add that root CA to a PEM file and point EPWgen to it.

Setting EPWGEN_CA_BUNDLE and EPWGEN_VERIFY (macOS / zsh)

- Export a CA bundle path for EPWgen to use (recommended):

```bash
# Single command to export in current shell
export EPWGEN_CA_BUNDLE="$HOME/certs/corp-root-ca.pem"
export EPWGEN_VERIFY=1

# To keep it for all shells, add the two lines to ~/.zshrc
```

- If you need to disable verification (debug only):

```bash
export EPWGEN_VERIFY=0
```

How to export a corporate root cert from Keychain (macOS GUI -> PEM)

1. Open Keychain Access.
2. Find the Root CA certificate your company uses (look under "System" or "System Roots").
3. Right-click the certificate → "Export".
4. Choose the format "Privacy Enhanced Mail (.pem)" and save it (e.g., ~/certs/corp-root-ca.pem).
5. Use the file path with `EPWGEN_CA_BUNDLE` as shown above.

Notes and security
- Prefer `EPWGEN_CA_BUNDLE` over disabling verification. Only set `EPWGEN_VERIFY=0` for short-term debugging.
- The code will default to the certifi bundle if `EPWGEN_CA_BUNDLE` is not set.

Example: run EPWgen with a corporate CA

```bash
export EPWGEN_CA_BUNDLE="$HOME/certs/corp-root-ca.pem"
export EPWGEN_VERIFY=1
python main.py
```

"""SSL / requests verify helper for EPWgen.

Provides a single place to derive the `verify` argument used by `requests` calls
from the environment variables:
- EPWGEN_CA_BUNDLE: path to PEM file to use as CA bundle
- EPWGEN_VERIFY: '0' or '1' (default 1) to disable verification for debugging

The function returns either:
- False (disable verification)
- a string path to a PEM file (use that bundle)
- the path returned by certifi.where() when no override is set
"""
import os
import sys
import certifi
import subprocess
import hashlib
import pathlib


def get_verify_arg():
    """Return a value suitable for `requests.get(..., verify=...)`.

    Raises FileNotFoundError if EPWGEN_CA_BUNDLE is set but the file doesn't exist.
    """
    ca_bundle = os.environ.get('EPWGEN_CA_BUNDLE')
    epwgen_verify = os.environ.get('EPWGEN_VERIFY', '1')

    if str(epwgen_verify).strip() in ('0', 'false', 'False'):
        return False

    if ca_bundle:
        if os.path.isfile(ca_bundle):
            return ca_bundle
        raise FileNotFoundError(f"EPWGEN_CA_BUNDLE is set to '{ca_bundle}' but the file does not exist.")

    # Default to certifi's bundle
    # On macOS, try to merge system roots into a single bundle so corporate root CAs are trusted
    if sys.platform == 'darwin':
        try:
            cache_dir = pathlib.Path.home() / '.epwgen'
            cache_dir.mkdir(parents=True, exist_ok=True)
            # Use a hash of certifi bundle and system trust command result to create a cache filename
            certifi_path = certifi.where()
            with open(certifi_path, 'rb') as f:
                certifi_hash = hashlib.sha256(f.read()).hexdigest()
            # Create a deterministic cache path
            merged_path = cache_dir / f'cacert-merged-{certifi_hash}.pem'
            if merged_path.exists():
                return str(merged_path)

            # Export system roots via security command
            proc = subprocess.run(['security', 'find-certificate', '-a', '-p'], capture_output=True, text=True)
            system_certs = proc.stdout
            if not system_certs:
                return certifi_path

            # Write merged file: certifi bundle first, then system certs
            with open(merged_path, 'wb') as out_f:
                with open(certifi_path, 'rb') as cf:
                    out_f.write(cf.read())
                out_f.write(b"\n")
                out_f.write(system_certs.encode('utf-8'))

            return str(merged_path)
        except Exception:
            return certifi.where()

    return certifi.where()

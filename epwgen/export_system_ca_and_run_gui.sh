#!/usr/bin/env bash
# Exports system Keychain certificates to a PEM and runs EPWgen GUI
# macOS only (uses `security find-certificate`)

set -euo pipefail

echo "Exporting system Keychain certificates to ~/.epwgen/system-certs.pem"
mkdir -p "$HOME/.epwgen"
SYSTEM_PEM="$HOME/.epwgen/system-certs.pem"

# Export all certificates from the system keychains into a single PEM
security find-certificate -a -p > "$SYSTEM_PEM"

echo "Wrote system certs to: $SYSTEM_PEM"

echo "Setting EPWGEN_CA_BUNDLE to $SYSTEM_PEM and enabling verification"
export EPWGEN_CA_BUNDLE="$SYSTEM_PEM"
export EPWGEN_VERIFY=1

echo "Launching EPWgen GUI using the EPWgen conda environment..."
if command -v conda >/dev/null 2>&1; then
  # Try to run in the EPWgen env; prefer conda's python
  conda run -n EPWgen /Users/cbianchi/opt/anaconda3/envs/EPWgen/bin/python -u main.py
else
  echo "conda not found in PATH. Please activate your EPWgen environment and run: python main.py"
fi

echo "Done"

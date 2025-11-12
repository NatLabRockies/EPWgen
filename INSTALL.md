# EPWgen Installation and Usage Guide

## Quick Install

### Option 1: Install from source (recommended for now)

```bash
cd /Users/cbianchi/Documents/GitHub/EPWgen
pip install -e .
```

This installs EPWgen in "editable" mode, so any changes you make to the code are immediately available.

### Option 2: Build and install as a package

```bash
cd /Users/cbianchi/Documents/GitHub/EPWgen
python -m build
pip install dist/epwgen-1.0.0-py3-none-any.whl
```

## Running EPWgen

After installation, you can run EPWgen from anywhere:

```bash
epwgen
```

Or with your conda environment:

```bash
conda activate nasa_power
epwgen
```

## Uninstall

```bash
pip uninstall epwgen
```

## Development

If you want to make changes and test:

```bash
cd /Users/cbianchi/Documents/GitHub/EPWgen
pip install -e .
```

Then just run `epwgen` to test your changes.

## Publishing to PyPI (Optional)

To make it available via `pip install epwgen` for everyone:

1. Create account on https://pypi.org
2. Install build tools: `pip install build twine`
3. Build: `python -m build`
4. Upload: `python -m twine upload dist/*`

Then anyone can install with: `pip install epwgen`

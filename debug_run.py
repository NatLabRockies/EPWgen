import sys, os
# ensure repo root is on sys.path
sys.path.insert(0, os.path.abspath('.'))

# Run the EPWgen main entrypoint
from epwgen.main import main

if __name__ == '__main__':
    main()

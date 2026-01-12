import sys, os
sys.path.insert(0, os.path.abspath('.'))
from epwgen.methods import run_individual_location

# Test parameters (small quick test)
lat = 39.05
lon = -84.6667
year = 2024
file_type = 'epw'
save_folder = '.'
save_name = 'TEST_NO_GUI'

print('Starting run_individual_location test...')
try:
    out = run_individual_location(lat, lon, year, file_type, save_folder, save_name)
    print('run_individual_location returned:')
    print(out)
except Exception as e:
    import traceback
    print('Exception during run_individual_location:')
    traceback.print_exc()

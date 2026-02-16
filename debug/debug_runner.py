#!/usr/bin/env python3
"""
Debug runner for EPWgen - Test specific locations with detailed logging
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path to import epwgen modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from epwgen.methods import run_individual_location, check_epw_quality, retrieve_distance_station_location


class DebugLogger:
    """Enhanced logging for debugging"""
    def __init__(self, log_file=None):
        self.log_file = log_file
        if log_file:
            # Create log file with timestamp
            os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
            with open(log_file, 'w') as f:
                f.write(f"=== EPWgen Debug Log - {datetime.now()} ===\n\n")
    
    def log(self, message, level="INFO"):
        """Log message to console and file"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] [{level}] {message}"
        print(formatted_msg)
        
        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(formatted_msg + "\n")
    
    def section(self, title):
        """Log a section header"""
        separator = "=" * 60
        self.log(f"\n{separator}")
        self.log(f"  {title}")
        self.log(f"{separator}\n")
    
    def step(self, step_num, description):
        """Log a step in the process"""
        self.log(f"STEP {step_num}: {description}", "STEP")
    
    def error(self, message):
        """Log an error"""
        self.log(f"❌ {message}", "ERROR")
    
    def success(self, message):
        """Log a success"""
        self.log(f"✓ {message}", "SUCCESS")
    
    def warning(self, message):
        """Log a warning"""
        self.log(f"⚠️  {message}", "WARNING")
    
    def data(self, label, value):
        """Log data with label"""
        self.log(f"  {label}: {value}", "DATA")


def run_debug_test(test_case, debug_output_dir, logger):
    """
    Run a single test case with detailed debugging
    """
    logger.section(f"Testing: {test_case['name']}")
    
    # Extract test parameters
    lat = test_case['latitude']
    lon = test_case['longitude']
    year = test_case['year']
    save_name = test_case['save_name']
    file_type = test_case.get('file_type', 'AMY')
    
    logger.data("Latitude", lat)
    logger.data("Longitude", lon)
    logger.data("Year", year)
    logger.data("Save Name", save_name)
    logger.data("File Type", file_type)
    logger.data("Notes", test_case.get('notes', 'N/A'))
    
    # Step 1: Retrieve weather data
    logger.step(1, "Retrieving weather data")
    try:
        result = run_individual_location(lat, lon, year, file_type, debug_output_dir, save_name)
        
        # Unpack results
        (retrieve_status, wmo, hdd, cdd, latitude_station, longitude_station, 
         retrieve_info_closest_other_locations, flags) = result
        
        logger.success("Data retrieval completed")
        logger.data("Status", retrieve_status)
        logger.data("WMO Station", wmo)
        logger.data("HDD (base 65F)", hdd)
        logger.data("CDD (base 65F)", cdd)
        logger.data("Station Latitude", latitude_station)
        logger.data("Station Longitude", longitude_station)
        logger.data("Flags", flags)
        
    except Exception as e:
        logger.error(f"Failed to retrieve weather data: {str(e)}")
        import traceback
        logger.log(traceback.format_exc(), "TRACEBACK")
        return False
    
    # Step 2: Check if EPW file was created
    logger.step(2, "Checking EPW file creation")
    epw_filename = f"{save_name.replace(' ', '_').replace('.', '_')}_{year}.epw"
    epw_path = os.path.join(debug_output_dir, epw_filename)
    
    if not os.path.isfile(epw_path):
        logger.error(f"EPW file not found: {epw_path}")
        return False
    
    logger.success(f"EPW file created: {epw_filename}")
    file_size = os.path.getsize(epw_path)
    logger.data("File size", f"{file_size:,} bytes")
    
    # Step 3: Calculate distance to station
    logger.step(3, "Calculating distance to weather station")
    try:
        distance_mi, lat_station, lon_station = retrieve_distance_station_location(wmo, lat, lon)
        logger.data("Distance to station", f"{distance_mi:.2f} miles")
        logger.data("Station coordinates", f"({lat_station}, {lon_station})")
    except Exception as e:
        logger.warning(f"Could not calculate distance: {str(e)}")
        distance_mi = None
    
    # Step 4: Run quality checks
    logger.step(4, "Running quality checks")
    try:
        quality_checks = check_epw_quality(epw_path)
        logger.success("Quality checks completed")
        for check_name, check_result in quality_checks.items():
            logger.data(check_name, check_result)
    except Exception as e:
        logger.error(f"Quality checks failed: {str(e)}")
        import traceback
        logger.log(traceback.format_exc(), "TRACEBACK")
        return False
    
    logger.section("Test Completed Successfully")
    return True


def main():
    """Main debug runner"""
    # Setup paths
    debug_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(debug_dir)
    test_config_path = os.path.join(debug_dir, "test_locations.json")
    debug_output_dir = os.path.join(debug_dir, "outputs")
    log_file = os.path.join(debug_dir, f"debug_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    
    # Create output directory
    os.makedirs(debug_output_dir, exist_ok=True)
    
    # Initialize logger
    logger = DebugLogger(log_file)
    logger.section("EPWgen Debug Runner Started")
    logger.data("Project Directory", project_dir)
    logger.data("Debug Directory", debug_dir)
    logger.data("Output Directory", debug_output_dir)
    logger.data("Log File", log_file)
    
    # Load test cases
    logger.step(0, "Loading test configuration")
    try:
        with open(test_config_path, 'r') as f:
            config = json.load(f)
        test_cases = config.get('test_cases', [])
        logger.success(f"Loaded {len(test_cases)} test cases")
    except FileNotFoundError:
        logger.error(f"Test configuration file not found: {test_config_path}")
        return 1
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in test configuration: {str(e)}")
        return 1
    
    # Filter enabled test cases
    enabled_tests = [tc for tc in test_cases if tc.get('enabled', True)]
    logger.data("Enabled tests", len(enabled_tests))
    
    if not enabled_tests:
        logger.warning("No enabled test cases found")
        return 0
    
    # Run tests
    results = []
    for i, test_case in enumerate(enabled_tests, 1):
        logger.log(f"\n{'=' * 60}")
        logger.log(f"Running test {i} of {len(enabled_tests)}")
        logger.log(f"{'=' * 60}\n")
        
        success = run_debug_test(test_case, debug_output_dir, logger)
        results.append({
            'name': test_case['name'],
            'success': success
        })
    
    # Summary
    logger.section("Debug Session Summary")
    successful = sum(1 for r in results if r['success'])
    failed = len(results) - successful
    
    logger.data("Total tests run", len(results))
    logger.data("Successful", successful)
    logger.data("Failed", failed)
    
    logger.log("\nTest Results:")
    for result in results:
        status = "✓ PASS" if result['success'] else "❌ FAIL"
        logger.log(f"  {status}: {result['name']}")
    
    logger.log(f"\n📝 Full log saved to: {log_file}")
    logger.log(f"📁 Output files saved to: {debug_output_dir}")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

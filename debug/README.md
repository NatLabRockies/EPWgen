# EPWgen Debug Tools

This folder contains debugging tools for testing and troubleshooting EPWgen functionality.

## Files

- **test_locations.json** - Configuration file with test cases for specific locations
- **debug_runner.py** - Debug script that runs test cases with detailed logging
- **outputs/** - Generated EPW files and debug outputs (created automatically)
- **debug_log_*.txt** - Timestamped log files with detailed execution traces

## Usage

### 1. Configure Test Locations

Edit `test_locations.json` to add or modify test cases:

```json
{
  "test_cases": [
    {
      "name": "My Test Case",
      "latitude": 40.0,
      "longitude": -76.0,
      "year": 2022,
      "save_name": "DEBUG_MyTest",
      "file_type": "AMY",
      "enabled": true,
      "notes": "Description of what you're testing"
    }
  ]
}
```

- Set `"enabled": true` to run a test case
- Set `"enabled": false` to skip it
- Add multiple test cases to run them sequentially

### 2. Run Debug Tests

From the EPWgen root directory:

```bash
python debug/debug_runner.py
```

Or from the debug directory:

```bash
cd debug
python debug_runner.py
```

### 3. Review Results

The script will:
- Print detailed progress to the console
- Save a complete log file: `debug_log_YYYYMMDD_HHMMSS.txt`
- Save EPW files to: `debug/outputs/`
- Show step-by-step execution with:
  - Data retrieval status
  - Weather station information
  - Distance calculations
  - Quality check results
  - Error tracebacks (if any)

### 4. Debugging Workflow

1. **Add failing location** to `test_locations.json`
2. **Run debug script** to see detailed logs
3. **Identify the problem** from step-by-step output
4. **Fix the issue** in `epwgen/methods.py` or `epwgen/main.py`
5. **Re-run debug script** to verify the fix
6. **Test with GUI** using the main `epwgen` command
7. **Commit changes** to the main codebase

### 5. Adding Custom Debug Points

To add more detailed logging in the main code, you can temporarily modify `epwgen/methods.py`:

```python
# Example: Add debug prints in methods.py
def some_function(params):
    print(f"DEBUG: Entering function with params: {params}")
    # ... existing code ...
    print(f"DEBUG: Intermediate result: {result}")
    # ... existing code ...
    return final_result
```

Then run the debug script to see these prints in context.

## Tips

- **Start simple**: Enable one test case at a time
- **Compare working vs failing**: Add both working and failing locations
- **Check logs**: The timestamped log files contain full tracebacks
- **Incremental testing**: Fix one issue at a time and re-test
- **Keep test cases**: Build a library of edge cases for regression testing

## Example Test Cases

### High Latitude Location
```json
{
  "name": "Arctic Location",
  "latitude": 71.2906,
  "longitude": -156.7886,
  "year": 2024,
  "save_name": "DEBUG_Barrow",
  "file_type": "AMY",
  "enabled": true,
  "notes": "Testing extreme northern latitude"
}
```

### Coastal Location
```json
{
  "name": "Coastal Test",
  "latitude": 25.7617,
  "longitude": -80.1918,
  "year": 2023,
  "save_name": "DEBUG_Miami",
  "file_type": "AMY",
  "enabled": true,
  "notes": "Testing coastal/tropical climate"
}
```

### Mountain Location
```json
{
  "name": "High Elevation",
  "latitude": 39.7392,
  "longitude": -104.9903,
  "year": 2022,
  "save_name": "DEBUG_Denver",
  "file_type": "AMY",
  "enabled": true,
  "notes": "Testing high elevation location"
}
```

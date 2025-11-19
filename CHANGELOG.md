# EPWgen Changelog

## [1.1.0] - 2025-11-13

### Added
- **New Mode: Download Metered Variables (NOAA Data Only)**
  - Fourth operational mode for downloading raw NOAA/Meteostat weather data
  - No EPW processing or MERRA-2 integration - pure measured data
  - Outputs raw hourly dataframe directly as CSV
  - Supports single year or multi-year downloads
  - **Multi-year data combined into single CSV file**
  - Single year: `LocationName_YEAR_metered.csv`
  - Multiple years: `LocationName_STARTYEAR-ENDYEAR_metered.csv`
  - Useful for custom analysis and processing workflows

### Changed
- Updated main GUI to include fourth button for metered variables download
- Added `MeteredVariablesDialog` for collecting location and year range input
- Multi-year downloads now combine all years into a single file instead of separate files

## [1.0.1] - 2025-11-12

### Added
- **Incremental CSV Progress Saving**: Progress is now saved after each successful EPW download instead of every 10 locations
- **Automatic Resume from Interruption**: When restarting a CSV batch job, EPWgen automatically:
  - Checks if a progress file exists in `outputs/[csv_name]/`
  - Loads from the progress file if found (resuming previous session)
  - Loads from the original CSV if no progress file exists (fresh start)
  - Shows informative message indicating resume mode
- **Enhanced Resilience**: Never lose work due to interruptions - all progress is continuously saved

### Changed
- CSV save frequency: Changed from every 10 locations to after each successful download
- CSV loading logic: Prioritizes existing progress file over original CSV file

### Fixed
- Dependency conflicts between pandas and isd package resolved
- NumPy version constrained to <2.0 for pandas 1.5.3 compatibility
- Installation now works cleanly with pandas 1.5.3 and numpy 1.26.4

## [1.0.0] - 2025-11-11

### Initial Release
- Three operational modes: Individual Location, Multi-Year Location, CSV Batch Processing
- Integration of MERRA-2 and Meteostat data sources
- Comprehensive quality checks and metadata output
- Interactive map visualization
- Skip existing files functionality
- Organized output folder structure


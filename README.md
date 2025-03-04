# EPWgen

EPWgen is a Python-based, cross-platform application for generating EnergyPlus Weather (EPW) files. With an intuitive graphical user interface (GUI), EPWgen allows users to create EPW files easily. The project is designed to work seamlessly on both macOS and Windows environments.

## Features

- **Cross-Platform Support:** Runs on macOS and Windows with minimal adjustments.
- **GUI Application:** User-friendly interface for managing EPW files.
- **Modular Code:** Organized into separate files for core functionality and methods.

## Requirements

- **Python:** Version 3.10 or later is recommended.
- **Dependencies:** 
  - [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro) (for GUI components)
  - Additional libraries as specified in `requirements.txt`

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/EPWgen.git
   cd EPWgen

   
## Set Up a Virtual Environment (Optional but Recommended)

```bash
python3.11 -m venv env
source env/bin/activate  # For Windows: env\Scripts\activate
```

## Install Required Packages

```bash
pip install -r requirements.txt
```

## Usage

To run EPWgen from the source code, execute:

```bash
python3.11 epwgen.py
```

## File Structure

- **epwgen.py**  
  This is the main entry point for the EPWgen application. It contains the GUI logic and ties together the overall functionality.

- **methods.py**  
  This file includes supporting functions and methods used throughout the application. It encapsulates core routines that are called from the main script.


# EPW File Metadata Description

## EPW_file_name_2023
This maps the EPW file name to the zip code.

## distance_location_station_miles_2023
Distance between the zip code centroid coordinates and the utilized weather station.

## weather_station_wmo_2023
Utilized weather station identifier.

## hdd_base65F_2023
Heating Degree Days for the selected EPW.

## cdd_base65F_2023
Cooling Degree Days for the selected EPW.

## Tdb_holes_2023
Tdb is being pulled from NOAA or other measured data sources. If there is any missing timestep, the corresponding value from MERRA2 is used. This flag informs if any MERRA2 data has been used to fill gaps.

## Tdew_holes_2023
Same as above but for Tdew.

## RH_holes_2023
Same as above but for RH.

## EnergyPlus Status
An EnergyPlus simulation has been run to verify that all the files executed correctly.

## Missing Data
Additional check to determine if the final EPW file contains any NaN values.

### Additional Temperature Checks:
- **Sudden Temp Jumps**  
- **Constant Temp Periods**  
- **Day-Night Swings**  
- **Summer Freezing**  
- **Winter Extreme Heat**  
- **Missing Temperature Data**
These are additional quality checks to detect anomalies or unusual patterns in the file. These tests are not used to discard files by default but serve as flags to review specific locations if issues arise when using the EPWs.



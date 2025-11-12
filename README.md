# EPWgen - Enhanced Weather File Generation

## Overview
EPWgen is a GUI tool designed to generate high-quality **EnergyPlus Weather (EPW) files** by integrating data from multiple reliable sources, improving accuracy, and addressing issues found in previous methods.

## Installation

### Quick Install
```bash
pip install -e /path/to/EPWgen
```

### Run the Application
```bash
epwgen
```

Or if using a conda environment:
```bash
conda activate your_environment
epwgen
```

## Usage Modes

EPWgen provides three operational modes through an intuitive GUI:

### 1. Individual Location
Generate an EPW file for a single location and year.
- Enter latitude, longitude, location name, and year
- Outputs saved to `outputs/` folder

### 2. Multi-Year Location
Generate EPW files for one location across multiple years.
- Enter latitude, longitude, location name, start year, and end year
- All files saved to `outputs/` folder

### 3. CSV Batch Processing
Process multiple locations from a CSV file.

**Required CSV Format:**
```csv
Latitude,Longitude,Location Name,Year
40.7128,-74.0060,New York,2022
34.0901,-118.4065,Beverly Hills,2022
41.8781,-87.6298,Chicago,2021
```

**Output:**
- EPW files saved to `outputs/[csv_filename]/`
- Updated CSV with metadata saved to same folder

### Data Sources:
#### **MERRA-2**
- Global dataset with data available everywhere, including **Alaska**
- **Near real-time availability**
- Provides **full EPWs** that act as the backbone
- **EPWgen swaps in key variables**:
  - **Tdb** (Dry Bulb Temperature)
  - **Tdew** (Dew Point Temperature)
  - **RH** (Relative Humidity)
  - **P** (Pressure)
  - **Wdir** (Wind Direction)
  - **Wspeed** (Wind Speed)
  - **Rain** (Precipitation)
  - **Snow**

#### **Meteostat**
- Free, open-source library: [Meteostat Documentation](https://dev.meteostat.net/)
- **Real-time data**
- **Expanded coverage (~2700 locations vs. ~1200)**
- **Data sources include**:
  - **National Weather Service**
  - **ISD (Global Dataset)**
  - **SYNOP reports**
  - **METAR reports**
  - **MOSMIX model data** (used for gap filling)

---

## Data Processing Workflow

1. **Find the closest Meteostat location** with < 3-hour data gaps.
2. **Gather the EPW file** from MERRA-2 based on selected station coordinates.
3. **Splice the two datasets** for enhanced accuracy.
4. **Insert metadata header**, including ASHRAE **2021 design conditions** and **ground temperatures**.
5. **Save the final EPW file** and output key metadata:
   - **Station distance**
   - **HDD/CDD (Heating & Cooling Degree Days)**
   - **Extreme Temperature Quality Checks**

---

## Output Metadata (CSV Batch Processing)

When processing CSV files, the following columns are added to track data quality and station information:

### **Status**
Indicates whether the EPW file was successfully retrieved.

### **Distance_Miles**
Distance between the requested location and the utilized weather station.

### **Station_WMO**
WMO code identifying the weather station used.

### **Station_Latitude** / **Station_Longitude**
Coordinates of the weather station.

### **HDD_base65F** / **CDD_base65F**
Heating and Cooling Degree Days (base 65°F) for the generated EPW.

### **Temp_Holes** / **Dewpoint_Holes** / **RH_Holes**
Flags indicating if MERRA-2 data was used to fill gaps in measured data for:
- **Temp_Holes**: Dry bulb temperature
- **Dewpoint_Holes**: Dew point temperature  
- **RH_Holes**: Relative Humidity

### **Quality Check Columns (QC_*)**
Multiple diagnostic columns identifying potential data anomalies:
- **QC_Missing_Data**: Checks for NaN values in the final EPW
- **QC_Extreme_Temperature**: Flags temperatures outside -50°C to 60°C
- **QC_Sudden_Temp_Jumps**: Detects temperature changes > 15°C per hour
- **QC_Constant_Temp_Periods**: Identifies periods with no temperature variation
- **QC_Day-Night_Swings**: Flags unrealistic daily temperature ranges
- **QC_Summer_Freezing**: Detects freezing temperatures in summer months
- **QC_Winter_Extreme_Heat**: Identifies extreme heat in winter months
- **QC_Missing_Temperature_Data**: Checks for missing temperature values

---

## Quality Check Details

Quality checks are **diagnostic tests** that flag potential anomalies for manual review. They do **not automatically discard files** but help identify data that may require closer inspection:

- **Extreme Values**: Temperatures outside physically reasonable ranges
- **Sudden Jumps**: Rapid temperature changes that may indicate sensor errors
- **Constant Periods**: Extended periods without temperature variation
- **Unrealistic Swings**: Daily temperature ranges that are too small or too large
- **Seasonal Mismatches**: Summer freezing or winter extreme heat events
- **Missing Data**: Gaps in temperature records

---

## Features

- **Skip Existing Files**: Automatically skips already-downloaded EPW files during batch processing
- **Progress Tracking**: Saves CSV progress every 10 locations to prevent data loss
- **Comprehensive Metadata**: Detailed quality checks and station information
- **Interactive Map**: View requested location vs. weather station location (individual mode)
- **Clean Output**: Organized folder structure with all files in `outputs/` directory

---

## Requirements

- Python 3.8+
- PyQt5
- pandas
- folium
- meteostat
- openstudio
- timezonefinder
- pytz
- requests

All dependencies are automatically installed via pip.

---

## License

MIT License

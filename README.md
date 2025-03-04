# EPWgen - Enhanced Weather File Generation

## Author: Carlo Bianchi  
### Last Updated: 09/12/2024  

## Overview
EPWgen is a tool designed to generate high-quality **EnergyPlus Weather (EPW) files** by integrating data from multiple reliable sources, improving accuracy, and addressing issues found in previous methods.

### Issues with Previous Methods:
- **Too slow**
- **Data quality issues**
- **No data above 60° latitude**
- **No data for past years**
- **No rain/snow data**
- **Superheavy repository size**
  
### Problems with `diyepw`:
- **Violates physics/psychrometry (TMY + AMY)**
- **Minimal or nonexistent quality control**
- **No relative humidity (RH)**
- **Limited data sources**

---

## EPWgen Solution
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

1. **Find the closest Meteostat location** with < 3-hour data gaps within 100 miles.
2. **Gather the EPW file** from MERRA-2 based on selected station coordinates.
3. **Splice the two datasets** for enhanced accuracy.
4. **Insert metadata header**, including ASHRAE **2021 design conditions**.
5. **Save the final EPW file** and output key metadata:
   - **Station distance**
   - **HDD/CDD (Heating & Cooling Degree Days)**

### Enhancements Over Previous Methods:
✅ **More locations covered**  
✅ **Built-in quality checks**  
✅ **All EPW variables filled with measured or modeled data**  
✅ **Latest completed year available**  
✅ **Global coverage (including high-latitude locations)**  
✅ **ASHRAE 2021 Design Conditions**  

---

## File Metadata Description

### **EPW_file_name_2023**
Maps the EPW file name to the corresponding zip code.

### **distance_location_station_miles_2023**
Distance between the zip code centroid coordinates and the utilized weather station.

### **weather_station_wmo_2023**
Identifies the utilized weather station.

### **hdd_base65F_2023**
Heating Degree Days for the selected EPW.

### **cdd_base65F_2023**
Cooling Degree Days for the selected EPW.

### **Tdb_holes_2023**
If any time steps are missing in NOAA/measured data, **MERRA-2 data is used** to fill gaps. This flag indicates if MERRA-2 replacements were applied.

### **Tdew_holes_2023**
Same as above but for **Tdew**.

### **RH_holes_2023**
Same as above but for **Relative Humidity (RH)**.

### **EnergyPlus Status**
Checks if an **EnergyPlus simulation** was successfully executed to validate file correctness.

### **Missing Data**
Verifies whether the **final EPW file contains any NaN values**.

---

## **Extreme Temperature Quality Checks**
These are **diagnostic tests** to identify anomalies in temperature data.  
They do **not automatically discard files** but flag them for manual review if needed.

- **Sudden Temperature Jumps**
- **Constant Temperature Periods**
- **Day-Night Temperature Swings**
- **Summer Freezing Events**
- **Winter Extreme Heat Events**
- **Missing Temperature Data**

---

## Future Improvements
EPWgen is actively evolving, with planned enhancements including:
- **Integration of TMY/GaTMY datasets**
- **Option to choose between ERA5 vs. MERRA-2**
- **Direct MERRA-2 data usage**
- **Data visualization and statistical outputs**
- **STAT file and/or DDYs creation**
- **Support for 2013 ASHRAE design conditions**
- **Search by FIP code or ZIP code**
- **Additional user-suggested features**

---

## Contributing
Contributions are welcome! Fork the repository and submit a pull request. For major changes, open an issue first to discuss your ideas.

## License
This project is licensed under the **MIT License**.

## Acknowledgements
Special thanks to the **open-source community** for providing tools like **PyQt5, Nuitka, PyInstaller, MERRA-2, and Meteostat**, making EPWgen possible.

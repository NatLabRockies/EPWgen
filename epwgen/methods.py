import os, sys, math, ssl, io, pytz, numpy as np, pandas as pd, requests
from datetime import datetime, timedelta, date
from timezonefinder import TimezoneFinder
from meteostat import Stations, Hourly
from isd import Batch
from scp import SCPClient
import paramiko, warnings, math, calendar, io, ssl
import pandas as pd
import numpy as np
from pandas.errors import EmptyDataError
import pytz
import subprocess
import shutil
import openstudio
import requests

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
import paramiko
import calendar
from pandas.errors import EmptyDataError
import shutil
import subprocess
import openstudio


import os
import pandas as pd

def check_epw_quality(epw_path):
    """
    Perform quality checks on an EPW file and return a summary of whether each variable is 'Good' or 'Suspicious'.

    Parameters:
        epw_path (str): Path to the EPW file.

    Returns:
        dict: Dictionary with quality check results for each tested variable.
    """

    # Force absolute path
    epw_path = os.path.abspath(epw_path)

    # Check if file exists
    if not os.path.isfile(epw_path):
        raise FileNotFoundError(f"❌ EPW file not found: {epw_path}")

    print('==================')
    print(f"Opening EPW: {epw_path}")

    # Read EPW file (skip header, start from line 9)
    epw_df = pd.read_csv(epw_path, skiprows=8, header=None)

    # Dictionary to store check results
    quality_checks = {}

    ### 1️⃣ Check for Missing Data ###
    missing_values = epw_df.isnull().sum().sum()
    quality_checks["Missing Data"] = "Suspicious" if missing_values > 0 else "Good"

    ### 2️⃣ Enhanced Dry Bulb Temperature Checks ###
    dry_bulb_temp = epw_df[6]  # Column 6 = Dry Bulb Temperature (°C)
    month = epw_df[1]          # Column 1 = Month
    day = epw_df[2]            # Column 2 = Day

    # Extreme temperature values (-50°C to 60°C)
    extreme_values = ((dry_bulb_temp < -50) | (dry_bulb_temp > 60)).any()
    quality_checks["Extreme Temperature"] = "Suspicious" if extreme_values else "Good"

    # Sudden jumps (> 15°C per hour)
    temp_diff = dry_bulb_temp.diff().abs()
    rapid_jumps = (temp_diff > 15).any()
    quality_checks["Sudden Temp Jumps"] = "Suspicious" if rapid_jumps else "Good"

    # Constant temperature for more than 12 hours
    const_periods = (dry_bulb_temp.rolling(window=12, min_periods=1).std() == 0).any()
    quality_checks["Constant Temp Periods"] = "Suspicious" if const_periods else "Good"

    # Unrealistic day-night swings (<3°C or >30°C)
    epw_df["daily_max"] = dry_bulb_temp.groupby(day).transform("max")
    epw_df["daily_min"] = dry_bulb_temp.groupby(day).transform("min")
    epw_df["daily_range"] = epw_df["daily_max"] - epw_df["daily_min"]
    unrealistic_swings = ((epw_df["daily_range"] < 3) | (epw_df["daily_range"] > 30)).any()
    quality_checks["Day-Night Swings"] = "Suspicious" if unrealistic_swings else "Good"

    # Seasonal mismatches
    summer_issues = ((month.isin([6, 7, 8])) & (dry_bulb_temp < 0)).any()
    winter_issues = ((month.isin([12, 1, 2])) & (dry_bulb_temp > 40)).any()
    quality_checks["Summer Freezing"] = "Suspicious" if summer_issues else "Good"
    quality_checks["Winter Extreme Heat"] = "Suspicious" if winter_issues else "Good"

    # Missing dry bulb temperature
    missing_temps = dry_bulb_temp.isna().any()
    quality_checks["Missing Temperature Data"] = "Suspicious" if missing_temps else "Good"

    return quality_checks


# def check_epw_quality(epw_path):
#     """
#     Perform quality checks on an EPW file and return a summary of whether each variable is 'Good' or 'Suspicious'.
    
#     Parameters:
#         epw_path (str): Path to the EPW file.
    
#     Returns:
#         dict: Dictionary with quality check results for each tested variable.
#     """

#     epw_path = os.path.abspath(epw_path)

#     print('==================')
#     print(epw_path)
#     # Read EPW file (skip header, start from line 9)
#     epw_df = pd.read_csv(epw_path, skiprows=8, header=None)

#     # Dictionary to store check results
#     quality_checks = {}

#     ### 1️⃣ Check for Missing Data ###
#     missing_values = epw_df.isnull().sum().sum()
#     quality_checks["Missing Data"] = "Suspicious" if missing_values > 0 else "Good"

#     ### 2️⃣ Enhanced Dry Bulb Temperature Checks ###
#     dry_bulb_temp = epw_df[6]
#     month = epw_df[1]

#     # Extreme values (-50°C to 60°C)
#     extreme_values = ((dry_bulb_temp < -50) | (dry_bulb_temp > 60)).any()
#     quality_checks["Extreme Temperature"] = "Suspicious" if extreme_values else "Good"

#     # Sudden jumps (> 15°C per hour)
#     temp_diff = dry_bulb_temp.diff().abs()
#     rapid_jumps = (temp_diff > 15).any()
#     quality_checks["Sudden Temp Jumps"] = "Suspicious" if rapid_jumps else "Good"

#     # Constant temperature for more than 12 hours
#     const_periods = (dry_bulb_temp.rolling(window=12, min_periods=1).std() == 0).any()
#     quality_checks["Constant Temp Periods"] = "Suspicious" if const_periods else "Good"

#     # Unrealistic day-night swings (<3°C or >30°C)
#     epw_df["daily_max"] = dry_bulb_temp.groupby(epw_df[2]).transform("max")
#     epw_df["daily_min"] = dry_bulb_temp.groupby(epw_df[2]).transform("min")
#     epw_df["daily_range"] = epw_df["daily_max"] - epw_df["daily_min"]
#     unrealistic_swings = ((epw_df["daily_range"] < 3) | (epw_df["daily_range"] > 30)).any()
#     quality_checks["Day-Night Swings"] = "Suspicious" if unrealistic_swings else "Good"

#     # Seasonal temperature mismatches
#     summer_issues = ((month.isin([6, 7, 8])) & (dry_bulb_temp < 0)).any()  # Summer months with freezing temps
#     winter_issues = ((month.isin([12, 1, 2])) & (dry_bulb_temp > 40)).any()  # Winter months with extreme heat
#     quality_checks["Summer Freezing"] = "Suspicious" if summer_issues else "Good"
#     quality_checks["Winter Extreme Heat"] = "Suspicious" if winter_issues else "Good"

#     # Missing temperature data
#     missing_temps = dry_bulb_temp.isna().any()
#     quality_checks["Missing Temperature Data"] = "Suspicious" if missing_temps else "Good"

#     return quality_checks

def run_energyplus_simulations(epw_path):
    
    # Set EnergyPlus installation location.
    energyplus_path = '/Applications/EnergyPlus-23-2-0/energyplus'
    current_directory = os.getcwd()

    # Create (or reuse) the simulation directory.
    out_dir = "test_epws_dir"
    os.makedirs(out_dir, exist_ok=True)

    min_idf_path = os.path.join(SCRIPT_DIR, "resources", "min.idf")
    min_idf = openstudio.IdfFile().load(min_idf_path).get()
    # Save IDF file
    min_idf.save(f"{out_dir}/in.idf", True)

    # Copy the minimal IDF file and the EPW file into the simulation directory.
    shutil.copy(epw_path, os.path.join(out_dir, "in.epw"))

    # Change directory to the simulation folder.
    os.chdir(out_dir)

    # Run EnergyPlus simulation.
    process = subprocess.run(
        [energyplus_path, "-w", "in.epw", "in.idf"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    
    # Check if the simulation ran successfully.
    status = "Good" if process.stderr.strip() == "EnergyPlus Completed Successfully." else "Bad"

    # Return to the original directory.
    os.chdir(current_directory)

    return status

def convert_utc_to_local(df, local_tz):
    """
    Convert the datetime index of the DataFrame from UTC to a local timezone.

    Args:
    df : pandas.DataFrame
        DataFrame with a datetime index in UTC.
    local_tz : str
        A timezone string (e.g., 'America/Chicago').

    Returns:
    pandas.DataFrame
        DataFrame with datetime index converted to the specified local timezone.
    """
    if not pd.api.types.is_datetime64_any_dtype(df.index):
        df = df.reset_index(level='station', drop=True)
        df.index = pd.to_datetime(df.index)

    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')
    
    df.index = df.index.tz_convert(local_tz)
    return df

def filter_dataframe_by_date(df, start_date, end_date, timezone=None):
    """
    Filter the DataFrame to include rows between the specified start and end dates,
    handling timezone differences appropriately.
    """
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    if timezone:
        start_date = start_date.tz_localize(timezone)
        end_date = end_date.tz_localize(timezone)
    else:
        df.index = df.index.tz_localize(None)

    return df.loc[(df.index >= start_date) & (df.index <= end_date)]

def get_parameters_MERRA2(lat, lon, year):
    api_endpoint = f"https://power.larc.nasa.gov/api/temporal/hourly/point?community=SB&parameters=&longitude={lon}&latitude={lat}&start={year}0101&end={year}1231&format=EPW"
    response = requests.get(api_endpoint)
    csv_data = io.StringIO(response.text)
    df = pd.read_csv(csv_data, skiprows=8, header=None)
    header = '\n'.join(response.text.splitlines()[:8])

    # Check if the dataframe has more than 8761 rows and truncate if necessary
    # Sometimes MERRA2 erroneously provides extra rows

    if calendar.isleap(int(year)):
        df = df.iloc[:8784]
    else:
        df = df.iloc[:8760]        


    return df, header

def merge_data(df, data):
    # Mapping of df column indices to the corresponding key names in data.
    columns_to_process = {
        6: 'temp',    # Dry bulb temperature
        7: 'dwpt',    # Dew point temperature
        8: 'rhum',    # Relative humidity
        33: 'prcp',   # Precipitation
        30: 'snow',   # Snow
        21: 'wspd',   # Wind speed
        20: 'wdir',   # Wind direction
        9: 'pres'     # Pressure
    }

    #Fix pressure units:
    # Check if df[9] is at least one order of magnitude (10x) higher than data['pres']
    if data['pres'].mean() != 0 and df[9].mean() >= 10 * data['pres'].mean():
        data['pres'] = data['pres'] * 100

    # Initialize flags for columns 6, 7, and 8.
    flags = {6: False, 7: False, 8: False}

    for df_col, data_key in columns_to_process.items():
        # Get the new values from data
        new_values = data[data_key]
       
        # Adjust the length of new_values to match df.
        if len(new_values) != len(df):
            if len(new_values) < len(df):
                # Reindex to the df index (or range) so missing timesteps become NaN.
                new_values = new_values.reindex(range(len(df)))
                # print(f"Data for key '{data_key}' was shorter than df; missing timesteps filled with NaN.")
            else:
                raise ValueError(f"There is something wrong in column {df_col} of MERRA2 data. Stopping execution.")



        # If processing one of the flagged columns, check for any holes (NaN values)
        if df_col in flags:
            # If any timestep in new_values is NaN, mark the flag as True.
            if new_values.isna().any():
                flags[df_col] = True

      
        # Replace values in df: where new_values is NaN, retain the original value.
        df[df_col] = new_values.where(new_values.notna(), df[df_col])

    # Return both the modified DataFrame and the flags dictionary.
    return df, flags

def check_missing_hours(year, df):
    """
    Checks for missing hours in the DataFrame's datetime index for a specified year.
    """
    full_index = pd.date_range(start=f"{year}-01-01", end=f"{year+1}-01-01", freq="H")
    missing_hours = full_index.difference(df.index)
    missing_hours_num = len(missing_hours)

    if missing_hours_num > 0:
        diffs = missing_hours.to_series().diff().dt.total_seconds().div(3600)
        largest_consecutive_group = (diffs != 1).cumsum().value_counts().max()
    else:
        largest_consecutive_group = 0

    return missing_hours_num, largest_consecutive_group

def add_datetime_index(df_merra2):
    # Rename columns 0-4 to the appropriate datetime names
    df_merra2_datetime = df_merra2[[0, 1, 2, 3, 4]].rename(
        columns={0: 'year', 1: 'month', 2: 'day', 3: 'hour', 4: 'minute'}
    )

    # Create the datetime index and assign it to the DataFrame
    df_merra2.index = pd.to_datetime(df_merra2_datetime)

    return df_merra2

def get_noaa_merra2_data(lat, lon, year, file_type, save_folder):
    """
    Retrieves NOAA and MERRA2 data for a specific location and year.
    """
    retrieve_status = True
    data_noaa, tz, elevation, wmo, station_name, state, country, latitude_station, longitude_station, epw_exists, incomplete_timeseries = get_data_noaa(lat, lon, year, save_folder)
    # data_noaa, tz, distance, elevation, wmo, station_name, state, country, latitude_station, longitude_station, epw_exists, incomplete_timeseries = get_data_noaa(lat, lon, year, save_folder)
    if epw_exists:
        df_merged = ''
        retrieve_status = False
        # distance = ''
        hdd = ''
        cdd = ''
        latitude_station = ''
        longitude_station = ''
        info_dict = ''
        epw_exists = True
        flags = ''
        # return df_merged, retrieve_status, info_dict, distance, hdd, cdd, wmo, latitude_station, longitude_station, epw_exists
        return df_merged, retrieve_status, info_dict, hdd, cdd, wmo, latitude_station, longitude_station, epw_exists, flags
    elif incomplete_timeseries:
        df_merged = ''
        retrieve_status = False
        # distance = np.nan
        hdd = ''
        cdd = ''
        latitude_station = ''
        longitude_station = ''
        info_dict = '' 
        wmo = ''
        epw_exists = False
        flags = ''
        # return df_merged, retrieve_status, info_dict, distance, hdd, cdd, wmo, latitude_station, longitude_station, epw_exists
        return df_merged, retrieve_status, info_dict, hdd, cdd, wmo, latitude_station, longitude_station, epw_exists, flags

    try:
        data_noaa_tz_adj = filter_dataframe_by_date(convert_utc_to_local(data_noaa, tz), datetime(year, 1, 1), datetime(year+1, 1, 1))
    except AttributeError:
        # print("We don't have NOAA data for this location/year")
        df_merged = ''
        retrieve_status = False
        # distance = np.nan
        hdd = ''
        cdd = ''
        latitude_station = ''
        longitude_station = ''
        info_dict = '' 
        epw_exists = False
        # return df_merged, retrieve_status, info_dict, distance, hdd, cdd, wmo, latitude_station, longitude_station, epw_exists
        return df_merged, retrieve_status, info_dict, hdd, cdd, wmo, latitude_station, longitude_station, epw_exists

    info_dict = {
    'timeshift': get_time_shift(tz),
    'elevation': elevation,
    'wmo': wmo,
    'station_name': station_name,
    'state': state,
    'country': country,
    'lat': latitude_station,
    'lon': longitude_station,
    'weather_file_type': file_type
    }

    data_noaa_tz_adj_h = data_noaa_tz_adj.resample('H').mean()
    data_noaa_tz_adj_h_interpolated = data_noaa_tz_adj_h.interpolate(method='linear', limit=3, limit_direction='both')
    hdd, cdd = calculate_hdd_cdd(data_noaa_tz_adj_h_interpolated, 'temp')
    try:
        df_merra2, header_merra2 = get_parameters_MERRA2(latitude_station, longitude_station, year)
    except EmptyDataError:
        try:
            df_merra2, header_merra2 = get_parameters_MERRA2(latitude_station, longitude_station, year)
        except EmptyDataError:
            try:
                df_merra2, header_merra2 = get_parameters_MERRA2(latitude_station, longitude_station, year)
            except EmptyDataError:
                try:
                    df_merra2, header_merra2 = get_parameters_MERRA2(latitude_station, longitude_station, year)
                except EmptyDataError:
                    df_merra2, header_merra2 = get_parameters_MERRA2(latitude_station, longitude_station, year)


    # add datetime index to MERRA2
    df_merra2 = add_datetime_index(df_merra2)
    

    #Remove the first row to align with MERRA2:
    # data_noaa_tz_adj_h_interpolated = data_noaa_tz_adj_h_interpolated[data_noaa_tz_adj_h_interpolated.index.year == year]
    data_noaa_tz_adj_h_interpolated = data_noaa_tz_adj_h_interpolated.iloc[1:]

    #Merge the 2 datasets
    [df_merged, flags] = merge_data(df_merra2, data_noaa_tz_adj_h_interpolated)

    # Check for empty cells in df_merged
    if df_merged.isnull().any().any():
        raise ValueError("The merged DataFrame (df_merged) contains empty cells. Stopping execution.")


    # return df_merged, retrieve_status, info_dict, distance, hdd, cdd, wmo, latitude_station, longitude_station, epw_exists
    return df_merged, retrieve_status, info_dict, hdd, cdd, wmo, latitude_station, longitude_station, epw_exists, flags

def run_individual_location(lat, lon, year, file_type, save_folder, save_name):
    """
    Processes a single location, fetching data and handling errors.
    """
    # data_meteostat_merra2, retrieve_status, info_dict, distance, hdd, cdd, wmo, latitude_station, longitude_station, epw_exists = get_noaa_merra2_data(lat, lon, year, file_type, save_folder)
    data_meteostat_merra2, retrieve_status, info_dict, hdd, cdd, wmo, latitude_station, longitude_station, epw_exists, flags = get_noaa_merra2_data(lat, lon, year, file_type, save_folder)
    
    if epw_exists:
        retrieve_status = False
        # distance = ''
        hdd = ''
        cdd = ''
        latitude_station = ''
        longitude_station = ''
        retrieve_info_closest_other_locations = True
    elif retrieve_status:
        retrieve_info_closest_other_locations = False
        #Save the EPW file
        if save_name != None:
            output_path = os.path.join(save_folder, f"{save_name.replace(' ', '_').replace('.', '_')}_{year}.epw")
        else:
            output_path = os.path.join(save_folder, f"{wmo}_{year}.epw")
        data_meteostat_merra2.to_csv(output_path, header=False, index=False)
        with open(output_path, 'r') as original_file:
            data_content = original_file.read()
        header_lines = create_header(data_meteostat_merra2, year, info_dict)
        with open(output_path, 'w') as new_file:
            new_file.write("\n".join(header_lines) + "\n" + data_content)
    else:
        retrieve_info_closest_other_locations = False
        retrieve_status = False
        print('No data available for this location/year.')

    # return retrieve_status, distance, wmo, hdd, cdd, latitude_station, longitude_station, retrieve_info_closest_other_locations
    return retrieve_status, wmo, hdd, cdd, latitude_station, longitude_station, retrieve_info_closest_other_locations, flags

def get_time_shift(timezone_name):
    """
    Calculates the time shift for a given timezone from UTC.
    """
    timezone = pytz.timezone(timezone_name)
    now = datetime.now(timezone)
    utc_offset = now.utcoffset()
    return int(utc_offset.total_seconds() // 3600)  # Return hours offset only

def calculate_hdd_cdd(df, temperature_column):
    """
    Calculate Heating Degree Days (HDD) and Cooling Degree Days (CDD) from hourly temperature data in Celsius.
    """
    df[temperature_column + '_F'] = df[temperature_column] * 9 / 5 + 32
    base_temperature = 65

    df['date'] = df.index.to_series().dt.date
    daily_mean_temp = df.groupby('date')[temperature_column + '_F'].mean().reset_index()
    daily_mean_temp.columns = ['date', 'mean_temp']

    daily_mean_temp['HDD'] = (base_temperature - daily_mean_temp['mean_temp']).clip(lower=0)
    daily_mean_temp['CDD'] = (daily_mean_temp['mean_temp'] - base_temperature).clip(lower=0)

    total_hdd = daily_mean_temp['HDD'].sum()
    total_cdd = daily_mean_temp['CDD'].sum()

    return int(total_hdd), int(total_cdd)

def check_epw_exists(save_folder, year, wmo):
    return os.path.exists(f'{save_folder}/{wmo}_{year}.epw')

def calc_combined_ground_temperatures(df):
    """
    Calculate shallow ground temperatures for multiple depths using the Kusuda and Achenbach model
    and format results as a single EPW GROUND TEMPERATURES line.
    This is the adapted version of the method used in ResStock:
    https://github.com/NREL/OpenStudio-HPXML/blob/master/HPXMLtoOpenStudio/resources/weather.rb#L315-L346

    Parameters:
        df (pd.DataFrame): DataFrame with hourly temperatures in column 6.

    Returns:
        str: Combined GROUND TEMPERATURES line in EPW file format for all depths.
    """
    depths = [0.5, 2, 4]  # Depths to consider (in meters)

    # Conversion utility
    def convert(value, from_unit, to_unit):
        if from_unit == "yr" and to_unit == "hr":
            return value * 365.25 * 24  # 1 year = 365.25 days * 24 hours
        elif from_unit == "C" and to_unit == "R":
            return (value + 273.15) * 9 / 5  # Celsius to Rankine
        elif from_unit == "R" and to_unit == "C":
            return (value - 491.67) * 5 / 9  # Rankine to Celsius
        elif from_unit == "C" and to_unit == "F":
            return value * 9 / 5 + 32  # Celsius to Fahrenheit
        elif from_unit == "F" and to_unit == "C":
            return (value - 32) * 5 / 9  # Fahrenheit to Celsius
        elif from_unit == "R" and to_unit == "F":
            return value - 459.67  # Rankine to Fahrenheit
        else:
            raise ValueError(f"Unsupported conversion from {from_unit} to {to_unit}")

    # Ensure proper datetime index
    df.index = pd.to_datetime({
        'year': df[0],
        'month': df[1],
        'day': df[2],
        'hour': df[3]
    })

    # Constants
    amon = [15.0, 46.0, 74.0, 95.0, 135.0, 166.0, 196.0, 227.0, 258.0, 288.0, 319.0, 349.0]  # Approx. mid-month days
    po = 0.6  # Phase offset
    dif = 0.025  # Thermal diffusivity (m²/hr)
    p = convert(1.0, 'yr', 'hr')  # Convert 1 year to hours

    # Use column 6 for temperatures
    df.rename(columns={6: 'Dry Bulb Temperature (°C)'}, inplace=True)

    # Calculate monthly and annual averages in Celsius
    monthly_avg_drybulbs_c = df.groupby(df.index.month)['Dry Bulb Temperature (°C)'].mean()
    annual_avg_drybulb_c = df['Dry Bulb Temperature (°C)'].mean()

    # Convert average temperatures to Rankine for decay calculations
    monthly_avg_drybulbs_r = monthly_avg_drybulbs_c.apply(lambda x: convert(x, 'C', 'R'))
    annual_avg_drybulb_r = convert(annual_avg_drybulb_c, 'C', 'R')

    # Prepare the combined GROUND TEMPERATURES line
    combined_ground_temperatures = ["GROUND TEMPERATURES", str(len(depths))]  # Start with header and number of depths

    for depth in depths:
        # Kusuda and Achenbach parameters
        beta = math.sqrt(math.pi / (p * dif)) * 10.0
        x = math.exp(-beta)
        s = math.sin(beta)
        c = math.cos(beta)
        y = (x**2 - 2.0 * x * c + 1.0) / (2.0 * beta**2.0)
        depth_factor = math.exp(-depth * math.sqrt(math.pi / (p * dif)))

        gm = math.sqrt(y) * depth_factor
        z = (1.0 - x * (c + s)) / (1.0 - x * (c - s))
        phi = math.atan(z)
        bo = (monthly_avg_drybulbs_r.max() - monthly_avg_drybulbs_r.min()) * 0.5

        # Calculate shallow ground temperatures
        shallow_ground_monthly_temps_r = []
        for i in range(12):  # Loop through 12 months
            theta = amon[i] * 24.0  # Day of the year to hours
            temp = annual_avg_drybulb_r - bo * math.cos(2.0 * math.pi / p * theta - po - phi) * gm
            shallow_ground_monthly_temps_r.append(temp)

        # Convert results to Celsius
        shallow_ground_monthly_temps_c = [convert(temp, 'R', 'C') for temp in shallow_ground_monthly_temps_r]

        # Add the depth, empty spaces, and monthly temperatures to the combined line
        combined_ground_temperatures.append(f"{depth:.1f}")
        combined_ground_temperatures.extend([""] * 3)  # Add three empty spaces
        combined_ground_temperatures.extend([f"{temp:.2f}" for temp in shallow_ground_monthly_temps_c])

    # Return the formatted line as a single string
    return ",".join(combined_ground_temperatures)

def create_header(df, year, info_dict):
    header_lines = []

    #Calculated parameters 
    first_day_year = pd.to_datetime(date.min.replace(year=year)).day_name()
    leap_status = lambda year: 'Yes' if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 'No'
    dst_start, dst_end = get_dst_start_end(year, info_dict['lat'], info_dict['lon'])
    design_conditions_file = os.path.join(SCRIPT_DIR, 'resources', 'design_conditions.csv')
    design_conditions_line = find_closest_design_condition(float(info_dict['lat']), float(info_dict['lon']), design_conditions_file)
    ground_temp_line = calc_combined_ground_temperatures(df)
    #Hardcoded parameters
    number_of_holidays = 0
    number_of_data_periods = 1
    number_of_records_per_hour = 1

    # line_1
    header_lines.append(f"LOCATION,{info_dict['station_name']},{info_dict['state']},{info_dict['country']},{info_dict['weather_file_type']},{info_dict['wmo']},{info_dict['lat']},{info_dict['lon']},{info_dict['timeshift']},{info_dict['elevation']}")
    # line_2
    header_lines.append(design_conditions_line)
    # line_3
    header_lines.append(f"TYPICAL/EXTREME PERIODS,0")
    # line_4
    header_lines.append(ground_temp_line)
    # header_lines.append(f"GROUND TEMPERATURES,0")
    # header_lines.append(f"GROUND TEMPERATURES,3,.5,,,,-16.34,-17.80,-15.22,-11.16,-0.57,7.61,13.13,14.81,11.95,5.60,-2.89,-10.76,2,,,,-10.97,-13.57,-13.04,-10.89,-3.80,2.61,7.74,10.49,9.90,6.30,0.46,-5.74,4,,,,-6.53,-9.19,-9.78,-8.97,-4.96,-0.64,3.32,6.08,6.72,5.16,1.73,-2.4")
    # line_5
    try:
        header_lines.append(f"HOLIDAYS/DAYLIGHT SAVINGS,{leap_status(year)},{dst_start.month}/{dst_start.day},{dst_end.month}/{dst_end.day},{number_of_holidays}")
    except AttributeError:
        #We cannot retrieve DST dates, let's set them to 0
        header_lines.append(f"HOLIDAYS/DAYLIGHT SAVINGS,{leap_status(year)},0,0,{number_of_holidays}")
    # line_6
    header_lines.append(f"COMMENTS 1, ")
    # line_7
    header_lines.append(f"COMMENTS 2, ")
    # line_8
    header_lines.append(f"DATA PERIODS,{number_of_data_periods},{number_of_records_per_hour},Data,{first_day_year},{df.iloc[0, 1]}/{df.iloc[0, 2]},{df.iloc[-1, 1]}/{df.iloc[-1, 2]}")

    return header_lines

def fix_wmo(wmo):
    """
    Attempts to fix or standardize the WMO code format.
    """
    try:
        return str(int(wmo))
    except ValueError:
        icao = wmo
        icao_converted = get_wmo_from_icao_NOAA(icao)
        if isinstance(icao_converted, type(None)):
            return icao
        else:
            return icao_converted

    # return wmo

def get_data_noaa(lat, lon, year, save_folder):
    """
    Fetches NOAA data for a given location and year, handling timezones and missing data.
    """
    # Disable SSL verification
    ssl._create_default_https_context = ssl._create_unverified_context

    start = datetime(year - 1, 12, 31)
    end = datetime(year + 1, 1, 2)

    stations = Stations().nearby(lat, lon)

    epw_exists = False
    station_number = 0
    len_data = 0

    incomplete_timeseries = True
    while incomplete_timeseries:
        station_number += 1
        wmo = fix_wmo(str(stations.fetch(station_number).index.values[-1]))
        # First check if EPW already exists
        if check_epw_exists(save_folder, year, wmo):
            epw_exists = True
            incomplete_timeseries = False
            break
        data = Hourly(stations.fetch(station_number), start, end, model=True).fetch()
        if (len(data.index) >100) & (station_number>1):
            data = data.loc[data.index.get_level_values('station').unique()[-1]]

        len_data = len(data.index)
        missing_hours_num, largest_consecutive_group = check_missing_hours(year, data)
        if (len_data > 8000) & (largest_consecutive_group <= 3):
            incomplete_timeseries = False

    if epw_exists | incomplete_timeseries:
        data = ''
        timezone = ''
        # distance = ''
        elevation = ''
        station_name = ''
        state = ''
        country = ''
        latitude_station = ''
        longitude_station = ''
                
    else:
        station_info = stations.fetch(station_number)
        timezone = station_info['timezone'].values[-1]
        elevation = station_info['elevation'].values[-1]
        # distance = stations.fetch()['distance'].values[-1]
        wmo = fix_wmo(str(station_info.index.values[-1]))
        station_name = (station_info['name'].values[-1]).replace(',', '_')
        state = station_info['region'].values[-1]
        country = station_info['country'].values[-1]
        latitude_station = station_info['latitude'].values[-1]
        longitude_station = station_info['longitude'].values[-1]

    # return data, timezone, distance, elevation, wmo, station_name, state, country, latitude_station, longitude_station, epw_exists,incomplete_timeseries
    return data, timezone, elevation, wmo, station_name, state, country, latitude_station, longitude_station, epw_exists,incomplete_timeseries

def update_if_missing(df, index, col_name, new_value):
    if col_name not in df.columns:
        df[col_name] = np.nan
    if pd.isna(df.at[index, col_name]) or not df.at[index, col_name]:
        df.at[index, col_name] = new_value

def retrieve_info_other_location(wmo, zipcodes, year):

    flags = {6: '', 7: '', 8: ''}

    retrieve_status = zipcodes[zipcodes[f"weather_station_wmo_{year}"]==str(wmo)][f"EPW_file_name_{year}"].values[0]
    # distance = zipcodes[zipcodes[f"weather_station_wmo_{year}"]==str(wmo)][f"distance_location_station_miles_{year}"].values[0]
    hdd = zipcodes[zipcodes[f"weather_station_wmo_{year}"]==str(wmo)][f"hdd_base65F_{year}"].values[0]
    cdd = zipcodes[zipcodes[f"weather_station_wmo_{year}"]==str(wmo)][f"cdd_base65F_{year}"].values[0]

    flags[6] = zipcodes[zipcodes[f"weather_station_wmo_{year}"]==str(wmo)][f"Tdb_holes_{year}"].values[0]
    flags[7] = zipcodes[zipcodes[f"weather_station_wmo_{year}"]==str(wmo)][f"Tdew_holes_{year}"].values[0]
    flags[8] = zipcodes[zipcodes[f"weather_station_wmo_{year}"]==str(wmo)][f"RH_holes_{year}"].values[0]
    # return retrieve_status, distance, hdd, cdd
    return retrieve_status, hdd, cdd, flags

def get_wmo_from_icao_NOAA(icao_code):
    # Path to the local CSV file in the resource folder
    csv_file_path = os.path.join(SCRIPT_DIR, 'resources', 'isd-history.csv')

    # Read the CSV file
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            headers = lines[0].split(',')
            icao_index = headers.index('"ICAO"')
            wmo_index = headers.index('"USAF"')

            for line in lines[1:]:
                fields = line.split(',')
                if fields[icao_index].strip('"') == icao_code.upper():
                    return fields[wmo_index].strip('"')

    except FileNotFoundError:
        print(f"CSV file not found at path: {csv_file_path}")
        return None
    except Exception as e:
        # print(f"An error occurred: {e}")
        return None

def get_dst_start_end(year, latitude, longitude):
    # Get the timezone for the given latitude and longitude
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lat=latitude, lng=longitude)
    
    if timezone_str is None:
        raise ValueError("Could not find timezone for the given coordinates.")
    
    # Get the timezone object
    timezone = pytz.timezone(timezone_str)
    
    # Define the dates for the beginning and end of the year (naive datetime)
    start_of_year = datetime(year, 1, 1)
    end_of_year = datetime(year, 12, 31)
    
    dst_start = None
    dst_end = None

    # Start by localizing the first date
    previous_offset = timezone.localize(start_of_year).dst()

    # Loop through each day of the year
    for dt in [start_of_year + timedelta(days=i) for i in range((end_of_year - start_of_year).days + 1)]:
        localized_dt = timezone.localize(dt)  # Localize naive datetime
        current_offset = localized_dt.dst()
        
        if previous_offset == timedelta(0) and current_offset != timedelta(0):
            dst_start = localized_dt
        elif previous_offset != timedelta(0) and current_offset == timedelta(0):
            dst_end = localized_dt
            break
        
        previous_offset = current_offset
    
    return dst_start, dst_end

# Function to calculate the distance between two points given their latitudes and longitudes
def haversine_distance(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1 
    dlon = lon2 - lon1 
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a)) 
    r = 6371  # Radius of Earth in kilometers. Use 3956 for miles. Determines return value units.

    #Distance returned in km
    return c * r

def find_closest_design_condition(lat,lon,design_conditions_file):
    """
    Finds the closest design condition from the CSV file based on the given latitude and longitude.

    Parameters:
    lat (float): The latitude of the target location.
    lon (float): The longitude of the target location.
    csv_file (str): The path to the CSV file containing design conditions.

    Returns:
    str: The 2021 design condition string for the closest location.
    """
    
    # Read the CSV file
    df = pd.read_csv(design_conditions_file)

    # Calculate distance from target coordinates to each row in the dataframe
    df['distance'] = df.apply(lambda row: haversine_distance(lat, lon, row['latitude'], row['longitude']), axis=1)

    # Find the row with the minimum distance
    closest_row = df.loc[df['distance'].idxmin()]

    # Return the design conditions for 2021
    return closest_row['2021_design_conditions']

def retrieve_distance_station_location(wmo, lat_location, lon_location):
    meteostat_stations_path = os.path.join(SCRIPT_DIR, 'resources', 'meteostat_stats.csv')
    meteostat_stations = pd.read_csv(meteostat_stations_path, index_col='id')
    lat_station = meteostat_stations[meteostat_stations.index == wmo]['latitude'].values[0]
    lon_station = meteostat_stations[meteostat_stations.index == wmo]['longitude'].values[0]
    distance_km = haversine_distance(lat_location, lon_location, lat_station, lon_station)
    distance_mi = distance_km*0.621371
    return distance_mi, lat_station, lon_station


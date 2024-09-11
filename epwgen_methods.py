import pandas as pd
import numpy as np
import paramiko
from scp import SCPClient
from isd import Batch
from meteostat import Stations, Hourly
from timezonefinder import TimezoneFinder
from datetime import datetime, timedelta, date
import pytz
import requests
import ssl
import io
import sys
import os



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
    return df, header

def merge_data(df, data):
    """
    Merges two datasets, replacing specific columns in `df` with corresponding values from `data`.
    """
    for col in [6, 7, 8, 33, 30, 21, 20, 9]:  # Replace indices with more descriptive names if possible
        if not df[col].isna().all():
            df[col] = list(data['temp'][1:])
    return df

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

def fix_wmo(wmo):
    """
    Attempts to fix or standardize the WMO code format.
    """
    if wmo:
        try:
            return str(int(wmo))
        except ValueError:
            icao = wmo
            return get_wmo_from_icao_NOAA(icao) or icao
    return wmo

def get_noaa_merra2_data(lat, lon, year, file_type, save_folder):
    """
    Retrieves NOAA and MERRA2 data for a specific location and year.
    """
    retrieve_status = True
    data_noaa, tz, distance, elevation, wmo, station_name, state, country, latitude_station, longitude_station, epw_exists, incomplete_timeseries = get_data_noaa(lat, lon, year, save_folder)

    if epw_exists:
        df_merged = ''
        retrieve_status = False
        distance = ''
        hdd = ''
        cdd = ''
        latitude_station = ''
        longitude_station = ''
        info_dict = ''
        epw_exists = True
        return df_merged, retrieve_status, info_dict, distance, hdd, cdd, wmo, latitude_station, longitude_station, epw_exists
    elif incomplete_timeseries:
        df_merged = ''
        retrieve_status = False
        distance = np.nan
        hdd = ''
        cdd = ''
        latitude_station = ''
        longitude_station = ''
        info_dict = '' 
        wmo = ''
        epw_exists = False
        return df_merged, retrieve_status, info_dict, distance, hdd, cdd, wmo, latitude_station, longitude_station, epw_exists

    try:
        data_noaa_tz_adj = filter_dataframe_by_date(convert_utc_to_local(data_noaa, tz), datetime(year, 1, 1), datetime(year+1, 1, 1))
    except AttributeError:
        # print("We don't have NOAA data for this location/year")
        df_merged = ''
        retrieve_status = False
        distance = np.nan
        hdd = ''
        cdd = ''
        latitude_station = ''
        longitude_station = ''
        info_dict = '' 
        epw_exists = False
        return df_merged, retrieve_status, info_dict, distance, hdd, cdd, wmo, latitude_station, longitude_station, epw_exists

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
    data_noaa_tz_adj_h_interpolated = data_noaa_tz_adj_h.interpolate(method='linear', limit=3, limit_direction='forward')
    hdd, cdd = calculate_hdd_cdd(data_noaa_tz_adj_h_interpolated, 'temp')

    df_merra2, header_merra2 = get_parameters_MERRA2(latitude_station, longitude_station, year)
    df_merged = merge_data(df_merra2, data_noaa_tz_adj_h_interpolated)

    return df_merged, retrieve_status, info_dict, distance, hdd, cdd, wmo, latitude_station, longitude_station, epw_exists

def run_individual_location(lat, lon, year, file_type, save_folder, save_name):
    """
    Processes a single location, fetching data and handling errors.
    """
    data_meteostat_merra2, retrieve_status, info_dict, distance, hdd, cdd, wmo, latitude_station, longitude_station, epw_exists = get_noaa_merra2_data(lat, lon, year, file_type, save_folder)
    if epw_exists:
        retrieve_status = False
        distance = ''
        hdd = ''
        cdd = ''
        latitude_station = ''
        longitude_station = ''
        retrieve_info_closest_other_locations = True
        # return retrieve_status, distance, info_dict['wmo'], hdd, cdd, latitude_station, longitude_station, retrieve_info_closest_other_locations
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

    return retrieve_status, distance, wmo, hdd, cdd, latitude_station, longitude_station, retrieve_info_closest_other_locations

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
    df[temperature_column] = df[temperature_column] * 9 / 5 + 32
    base_temperature = 65

    df['date'] = df.index.to_series().dt.date
    daily_mean_temp = df.groupby('date')[temperature_column].mean().reset_index()
    daily_mean_temp.columns = ['date', 'mean_temp']

    daily_mean_temp['HDD'] = (base_temperature - daily_mean_temp['mean_temp']).clip(lower=0)
    daily_mean_temp['CDD'] = (daily_mean_temp['mean_temp'] - base_temperature).clip(lower=0)

    total_hdd = daily_mean_temp['HDD'].sum()
    total_cdd = daily_mean_temp['CDD'].sum()

    return int(total_hdd), int(total_cdd)

def check_epw_exists(save_folder, year, wmo):
    return os.path.exists(f'{save_folder}/{wmo}_{year}.epw')

def create_header(df, year, info_dict):
    header_lines = []

    #Calculated parameters 
    first_day_year = pd.to_datetime(date.min.replace(year=year)).day_name()
    leap_status = lambda year: 'Yes' if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 'No'
    dst_start, dst_end = get_dst_start_end(year, info_dict['lat'], info_dict['lon'])
    design_conditions_file = 'resources/design_conditions.csv'
    design_conditions_line = find_closest_design_condition(float(info_dict['lat']), float(info_dict['lon']), design_conditions_file)
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
    header_lines.append(f"GROUND TEMPERATURES,0")
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
        len_data = len(data)
        missing_hours_num, largest_consecutive_group = check_missing_hours(year, data)
        if (len_data > 8000) & (largest_consecutive_group <= 3):
            incomplete_timeseries = False
        distance = stations.fetch(station_number)['distance'].values[-1]
        # Let's stop after 100mi
        if distance > 160000:
            break

    if epw_exists | incomplete_timeseries:
        data = ''
        timezone = ''
        distance = ''
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
        distance = stations.fetch()['distance'].values[-1]
        wmo = fix_wmo(str(station_info.index.values[-1]))
        station_name = station_info['name'].values[-1]
        state = station_info['region'].values[-1]
        country = station_info['country'].values[-1]
        latitude_station = station_info['latitude'].values[-1]
        longitude_station = station_info['longitude'].values[-1]

    return data, timezone, distance, elevation, wmo, station_name, state, country, latitude_station, longitude_station, epw_exists,incomplete_timeseries

# Helper function to check and update missing data
def update_if_missing(df, index, col_name, new_value):
    if pd.isna(df.at[index, col_name]) or not df.at[index, col_name]:
        df.at[index, col_name] = new_value

def retrieve_info_other_location(wmo, zipcodes, year):
    retrieve_status = zipcodes[zipcodes[f"weather_station_wmo_{year}"]==str(wmo)][f"Do we have data for {year}?"].values[0]
    distance = zipcodes[zipcodes[f"weather_station_wmo_{year}"]==str(wmo)][f"distance_location_station_miles_{year}"].values[0]
    hdd = zipcodes[zipcodes[f"weather_station_wmo_{year}"]==str(wmo)][f"hdd_base65F_{year}"].values[0]
    cdd = zipcodes[zipcodes[f"weather_station_wmo_{year}"]==str(wmo)][f"cdd_base65F_{year}"].values[0]
    return retrieve_status, distance, hdd, cdd

def get_wmo_from_icao_NOAA(icao_code):
    # URL to the NOAA ISD database metadata
    url = "https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv"
    
    # Fetch the data
    response = requests.get(url)
    
    if response.status_code == 200:
        # Read the CSV data
        csv_data = response.content.decode('utf-8')
        
        # Parse the CSV data
        lines = csv_data.splitlines()
        headers = lines[0].split(',')
        icao_index = headers.index('"ICAO"')
        wmo_index = headers.index('"USAF"')

        for line in lines[1:]:
            fields = line.split(',')
            if fields[icao_index].strip('"') == icao_code.upper():
                return fields[wmo_index].strip('"')
    else:
        print(f"Failed to retrieve data, status code: {response.status_code}")
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
        return c * r

    
    # Read the CSV file
    df = pd.read_csv(design_conditions_file)

    # Calculate distance from target coordinates to each row in the dataframe
    df['distance'] = df.apply(lambda row: haversine_distance(lat, lon, row['latitude'], row['longitude']), axis=1)

    # Find the row with the minimum distance
    closest_row = df.loc[df['distance'].idxmin()]

    # Return the design conditions for 2021
    return closest_row['2021_design_conditions']

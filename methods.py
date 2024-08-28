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
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QTextEdit, QPushButton, QVBoxLayout, QGridLayout, QMessageBox
)




def get_data_noaa(lat, lon, year):
    #  The time zone used by Meteostat is Coordinated Universal Time (UTC).
    # Disable SSL verification
    ssl._create_default_https_context = ssl._create_unverified_context

    start = datetime(year-1, 12, 31)
    end = datetime(year+1, 1, 2)

    # Use certifi's CA bundle
    # ssl_context = ssl.create_default_context(cafile=certifi.where())
    # Find the closest station
    stations = Stations().nearby(lat, lon) 
    # Get hourly data for the first station
    data = Hourly(stations.fetch(1), start, end, model=True).fetch()
    timezone = stations.fetch(1)['timezone'].values[0]
    #elevation in meters
    elevation = stations.fetch(1)['elevation'].values[0]
    #Distance in m
    distance = stations.fetch()['distance'].values[0]
    #WMO
    wmo = str(stations.fetch(1).index.values[0])
    #Station Name
    station_name = stations.fetch()['name'].values[0]
    #State
    state = stations.fetch()['region'].values[0]
    #Country
    country = stations.fetch()['country'].values[0]

    return data, timezone, distance, elevation, wmo, station_name, state, country

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
    # Ensure the index is timezone-aware, set to UTC
    if df.index.tz is None:
        df.index = df.index.tz_localize('UTC')

    # Convert the timezone of the index
    df.index = df.index.tz_convert(local_tz)
    return df

def filter_dataframe_by_date(df, start_date, end_date, timezone=None):
    """
    Filter the DataFrame to include rows between the specified start and end dates,
    handling timezone differences appropriately.

    Args:
    df : pandas.DataFrame
        DataFrame with a datetime index.
    start_date : str or datetime-like
        The beginning date of the interval to filter the DataFrame.
    end_date : str or datetime-like
        The end date of the interval to filter the DataFrame.
    timezone : str, optional
        The timezone to which to convert the dates before filtering,
        if the datetime index is timezone-aware.

    Returns:
    pandas.DataFrame
        DataFrame filtered to include only rows between the specified dates.
    """
    # Convert string dates to datetime, considering the timezone
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    if timezone:
        # Convert dates to the specified timezone if provided
        start_date = start_date.tz_localize(timezone)
        end_date = end_date.tz_localize(timezone)
    else:
        # Make datetime index timezone-naive if no timezone is specified
        df.index = df.index.tz_localize(None)

    # Filter the DataFrame
    mask = (df.index >= start_date) & (df.index <= end_date)
    return df.loc[mask]

def get_parameters_MERRA2(lat, lon, year):
    api_endpoint = f"https://power.larc.nasa.gov/api/temporal/hourly/point?community=SB&parameters=&longitude={lon}&latitude={lat}&start={year}0101&end={year}1231&format=EPW"
    response = requests.get(api_endpoint)
    # Split the response text into lines
    lines = response.text.splitlines()
    header = ('\n'.join(lines[:8]))
    # Convert back into a file-like object
    csv_data = io.StringIO('\n'.join(lines))
    # Read into a pandas DataFrame
    df = pd.read_csv(csv_data, skiprows=8, header=None)
    return df, header

def merge_data(df, data):

    if not df[6].isna().all():
        df[6] = list(data['temp'][1:])
    if not df[7].isna().all():
        df[7] = list(data['temp'][1:])
    if not df[8].isna().all():
        df[8] = list(data['temp'][1:])
    if not df[33].isna().all():
        df[33] = list(data['temp'][1:])
    if not df[30].isna().all():
        df[30] = list(data['temp'][1:])
    if not df[21].isna().all():
        df[21] = list(data['temp'][1:])
    if not df[20].isna().all():
        df[20] = list(data['temp'][1:])
    if not df[9].isna().all():
        df[9] = list(data['temp'][1:])

    return df

def check_missing_hours(year, df):
    # Generate a complete set of hourly timestamps for the entire year
    full_index = pd.date_range(start=f"{year}-01-01 00:00:00", end=f"{year+1}-01-01 00:00:00", freq="h")
    # Find the missing hours by comparing the complete set with the dataframe's index
    missing_hours = full_index.difference(df.index)
    # Calculate the number of missing hours
    missing_hours_num = len(missing_hours)
    # Find the size of the largest group of consecutive missing hours
    if missing_hours_num > 0:
        # Calculate the difference between consecutive missing hours
        diffs = missing_hours.to_series().diff().dt.total_seconds().div(3600)
        # Identify the groups where the difference between consecutive hours is 1 (consecutive hours)
        consecutive_groups = (diffs != 1).cumsum()
        # Find the size of the largest group of consecutive missing hours
        largest_consecutive_group = consecutive_groups.value_counts().max()
    else:
        largest_consecutive_group = 0
    return missing_hours_num, largest_consecutive_group

def get_noaa_merra2_data(lat, lon, year,file_type):
    missing_dates = False
    # The time zone used by Meteostat is Coordinated Universal Time (UTC).
    data_noaa, tz, distance, elevation, wmo, station_name, state, country = get_data_noaa(lat, lon, year)
    #If Meteostat returns not a WMO, check the correspondoing WMO from NOAA
    try:
        wmo = str(int(wmo))
    except ValueError:
        wmo = get_wmo_from_icao_NOAA(wmo)
        
    # Create the dictionary
    info_dict = {
        'timeshift': get_time_shift(tz),
        'elevation': elevation,
        'wmo': wmo,
        'station_name': station_name,
        'state': state,
        'country': country,
        'lat': lat,
        'lon': lon,
        'weather_file_type': file_type
        }

    # Adjust timezone and cut from 1/1 to 12/31
    data_noaa_tz_adj = filter_dataframe_by_date(convert_utc_to_local(data_noaa, tz ), datetime(year, 1, 1), datetime(year+1, 1, 1))
    #Check if there are missing hours:
    missing_hours_num, largest_consecutive_group = check_missing_hours(year, data_noaa_tz_adj)
    if largest_consecutive_group>3:
        missing_dates = True
        df_merged = []
    else:
        # Resample the dataframe to hourly frequency
        data_noaa_tz_adj_h = data_noaa_tz_adj.resample('h').mean()
        # Linearly interpolate missing values, limiting to 3 consecutive missing hours
        data_noaa_tz_adj_h_interpolated = data_noaa_tz_adj_h.interpolate(method='linear', limit=3, limit_direction='forward')

        #get data MERRA2
        df_merra2, header_merra2 = get_parameters_MERRA2(lat, lon, year)
        #Merge two datasets
        df_merged = merge_data(df_merra2, data_noaa_tz_adj_h_interpolated)
    return df_merged, missing_dates, info_dict

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

def find_closest_design_condition(lat, lon,design_conditions_file):
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

def create_header(df, year, info_dict):
    header_lines = []

    #Calculated parameters 
    first_day_year = pd.to_datetime(date.min.replace(year=year)).day_name()
    leap_status = lambda year: 'Yes' if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 'No'
    dst_start, dst_end = get_dst_start_end(year, lat, lon)
    design_conditions_file = 'resources/design_conditions.csv'
    design_conditions_line = find_closest_design_condition(float(info_dict['lat']), float(info_dict['lon']), design_conditions_file)
    #Hardcoded parameters
    number_of_holidays = 0
    number_of_data_periods = 1
    number_of_records_per_hour = 1

    # line_1
    header_lines.append(f"LOCATION,{info_dict['station_name']},{info_dict['state']},{info_dict['country']},{info_dict['weather_file_type']},{info_dict['wmo']},{info_dict['lat']},{info_dict['lon']},{info_dict['timeshift']},{info_dict['elevation']}")
    # line_2
    header_lines.append(info_dict['design_conditions'])
    # line_3
    header_lines.append(f"TYPICAL/EXTREME PERIODS,6,Summer - Week Nearest Max Temperature For Period,Extreme,7/20,7/26,Summer - Week Nearest Average Temperature For Period,Typical,6/22,6/28,Winter - Week Nearest Min Temperature For Period,Extreme,12/ 1,12/ 7,Winter - Week Nearest Average Temperature For Period,Typical,1/27,2/ 2,Autumn - Week Nearest Average Temperature For Period,Typical,10/13,10/19,Spring - Week Nearest Average Temperature For Period,Typical,4/12,4/18")
    # line_4
    header_lines.append(f"GROUND TEMPERATURES,3,.5,,,,-16.34,-17.80,-15.22,-11.16,-0.57,7.61,13.13,14.81,11.95,5.60,-2.89,-10.76,2,,,,-10.97,-13.57,-13.04,-10.89,-3.80,2.61,7.74,10.49,9.90,6.30,0.46,-5.74,4,,,,-6.53,-9.19,-9.78,-8.97,-4.96,-0.64,3.32,6.08,6.72,5.16,1.73,-2.4")
    # line_5
    header_lines.append(f"HOLIDAYS/DAYLIGHT SAVINGS,{leap_status(year)},{dst_start.month}/{dst_start.day},{dst_end.month}/{dst_end.day},{number_of_holidays}")
    # line_6
    header_lines.append(f"COMMENTS 1, ")
    # line_7
    header_lines.append(f"COMMENTS 2, ")
    # line_8
    header_lines.append(f"DATA PERIODS,{number_of_data_periods},{number_of_records_per_hour},Data,{first_day_year},{df.iloc[0, 1]}/{df.iloc[0, 2]},{df.iloc[-1, 1]}/{df.iloc[-1, 2]}")

    return header_lines

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

def get_time_shift(timezone_name):
    # Get the timezone object
    timezone = pytz.timezone(timezone_name)
    # Get the current time in that timezone
    now = datetime.now(timezone)
    # Retrieve the UTC offset
    utc_offset = now.utcoffset()
    # Convert the offset to hours and minutes
    total_minutes = utc_offset.total_seconds() / 60
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    
    return hours



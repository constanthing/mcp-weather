"""
pip3 install openmeteo-requests pandas requests-cache retry-requests requests

(for printing dataframe as markdown)
pip3 install tabulate
"""

import json

import openmeteo_requests

import pandas as pd
import requests_cache
from retry_requests import retry
import requests

import datetime
import sqlite3
from typing import List, Dict, Any, Optional

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

def get_coordinates(location: str, state: str):
    LOCATE_URL = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=10&language=en&format=json&countryCode=US"
    response = requests.get(LOCATE_URL)
    response = response.json()

    if "results" in response:
        for result in response['results']:
            if result['admin1'] == state:
                return {"latitude": result['latitude'], "longitude": result['longitude']}

        return None
    else:
        return None



# functions (tools) the ai model can call

def get_hourly_forecast(location: str, state: str, forecast_days = 1, latitude: float = None, longitude: float = None, start_hour: int = None, end_hour: int = None):
    """
    Default unit is fahrenheit because US is only supported.
    """

    try:
        print("!!!!!!!Get Hourly Forecast!!!!!!!")
        print(location, state, int(forecast_days))

        if latitude is None or longitude is None:
            coordinates = get_coordinates(location, state)
            if coordinates is None:
                return f"Sorry, I don't have coordinates for {location.capitalize()} in {state}."
            else:
                latitude, longitude = coordinates['latitude'], coordinates['longitude']

        print(latitude, longitude)

        URL    = "https://api.open-meteo.com/v1/forecast"
        PARAMS = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ["temperature_2m", "precipitation_probability", "relative_humidity_2m", "cloud_cover", "wind_speed_10m", "wind_gusts_10m", "apparent_temperature"],
            "forecast_days": int(forecast_days),
            "wind_speed_unit": "mph",
            "temperature_unit": "fahrenheit",
            "precipitation_unit": "inch",
            "timezone": "America/New_York",
            # todo: look into adding set timezone functionality 
        }
        responses = openmeteo.weather_api(URL, params=PARAMS)

        hourly = responses[0].Hourly()

        print(f"Variables length: {hourly.VariablesLength()}")

        temperature_2m = hourly.Variables(0).ValuesAsNumpy().tolist()
        precipitation_probability = hourly.Variables(1).ValuesAsNumpy().tolist()
        relative_humidity_2m = hourly.Variables(2).ValuesAsNumpy().tolist()
        cloud_cover = hourly.Variables(3).ValuesAsNumpy().tolist()
        wind_speed_10m = hourly.Variables(4).ValuesAsNumpy().tolist()
        wind_gusts_10m = hourly.Variables(5).ValuesAsNumpy().tolist()
        apparent_temperature = hourly.Variables(6).ValuesAsNumpy().tolist()

        hourly_data = {"date": pd.date_range(
            start = pd.to_datetime(hourly.Time(), unit = "s", utc=True).tz_convert('America/New_York'),
            end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc=True).tz_convert('America/New_York'),
            freq = pd.Timedelta(seconds = hourly.Interval()),
            inclusive = "left"
        )}

        # round each value in temperature_2m array
        hourly_data["temperature_2m_fahrenheit"] = [round(x) for x in temperature_2m]
        hourly_data["precipitation_probability_percent"] = precipitation_probability
        hourly_data["relative_humidity_2m_percent"] = relative_humidity_2m
        hourly_data["cloud_cover_percent"] = cloud_cover
        hourly_data["wind_speed_10m_mph"] = [round(x) for x in wind_speed_10m]
        hourly_data["wind_gusts_10m_mph"] = [round(x) for x in wind_gusts_10m]
        hourly_data["apparent_temperature_fahrenheit"] = [round(x) for x in apparent_temperature]

        hourly_dataframe = pd.DataFrame(data = hourly_data)
        
        # Add additional columns to the DataFrame
        hourly_dataframe['year'] = hourly_dataframe['date'].dt.year
        hourly_dataframe['month'] = hourly_dataframe['date'].dt.month
        hourly_dataframe['day'] = hourly_dataframe['date'].dt.day
        hourly_dataframe['hour_24'] = hourly_dataframe['date'].dt.hour
        hourly_dataframe['hour_12'] = hourly_dataframe['date'].dt.strftime('%I')
        hourly_dataframe['minute'] = hourly_dataframe['date'].dt.minute
        hourly_dataframe['second'] = hourly_dataframe['date'].dt.second
        hourly_dataframe['day_of_week'] = hourly_dataframe['date'].dt.strftime('%A')
        hourly_dataframe['am_pm'] = hourly_dataframe['date'].dt.strftime('%p')
        
        print("==========OPEN METEO DATA =============")
        print(json.dumps(hourly_dataframe.to_markdown()))
        print(hourly_dataframe.to_json())
        print("=======================")
        # return hourly_dataframe.to_json()
        return hourly_dataframe.to_markdown()
    except Exception as e:
        print(e)
        return f"Sorry, an error occurred in get_hourly_forecast: {e}"


def get_coordinates_of_location(location: str, state: str):
    """
    Currently only support US locations
    * api docs: https://open-meteo.com/en/docs/geocoding-api?name=Lehigh+Acres&countryCode=US
    """
    print(location, state)
    try:
        coordinates = get_coordinates(location, state)

        if coordinates is None:
            return f"Sorry, I don't have coordinates for {location.capitalize()} in {state}."
        else:
            return coordinates
            return f"The coordinates of {location.capitalize()} in {state} are {coordinates['latitude']}, {coordinates['longitude']}."
    except Exception as e:
        print(e)
        return f"Sorry, an error occurred in get_coordinates_of_location: {e}"

def filter_weather_data_sql(weather_data: List[Dict], query: str) -> List[Dict]:
    """
    Filter weather data using SQL queries on an in-memory SQLite database.
    
    Args:
        weather_data: List of weather data dictionaries
        query: SQL query to filter the data (e.g., "SELECT * FROM weather WHERE temperature_2m < 82 AND wind_speed_10m < 15")
    
    Returns:
        Filtered list of weather data dictionaries
    """
    if not weather_data:
        return []
    
    # Create in-memory SQLite database
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    try:
        # Create table from the first data point
        first_item = weather_data[0]['date']
        columns = list(first_item.keys())
        
        # Create table schema
        column_definitions = []
        for col in columns:
            if col in ['timestamp', 'year', 'month', 'day', 'hour', 'minute', 'second']:
                column_definitions.append(f"{col} INTEGER")
            elif col in ['temperature_2m', 'precipitation_probability', 'relative_humidity_2m', 
                        'cloud_cover', 'wind_speed_10m', 'wind_gusts_10m', 'apparent_temperature']:
                column_definitions.append(f"{col} REAL")
            else:
                column_definitions.append(f"{col} TEXT")
        
        create_table_sql = f"""
        CREATE TABLE weather (
            {', '.join(column_definitions)}
        )
        """
        cursor.execute(create_table_sql)
        
        # Insert data
        for item in weather_data:
            values = [item['date'][col] for col in columns]
            placeholders = ', '.join(['?' for _ in columns])
            insert_sql = f"INSERT INTO weather ({', '.join(columns)}) VALUES ({placeholders})"
            cursor.execute(insert_sql, values)
        
        # Execute the user's query
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Convert back to dictionary format
        filtered_data = []
        for row in results:
            row_dict = {}
            for i, col in enumerate(columns):
                row_dict[col] = row[i]
            
            filtered_data.append({"date": row_dict})
        
        return filtered_data

        
    finally:
        conn.close()

def get_weather_filtered_sql(location: str, state: str, forecast_days: int = 1, 
                           start_hour: int = None, end_hour: int = None, 
                           sql_filter: str = None, **kwargs) -> List[Dict]:
    """
    Get weather data and optionally filter it using SQL queries.
    
    Args:
        location: City name
        state: State name
        forecast_days: Number of days to forecast
        start_hour: Start hour for filtering (0-23)
        end_hour: End hour for filtering (0-23)
        sql_filter: SQL WHERE clause for filtering (e.g., "temperature_2m < 82 AND wind_speed_10m < 15")
    
    Returns:
        Filtered weather data
    """
    data = get_hourly_forecast(location, state, forecast_days, start_hour=start_hour, end_hour=end_hour)
    
    if isinstance(data, str):  # Error message
        return data
    
    if sql_filter:
        # Apply SQL filtering
        query = f"SELECT * FROM weather WHERE {sql_filter}"
        return filter_weather_data_sql(data, query)
    
    return data

def filter_weather_data_pandas(weather_data: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
    """
    Filter weather data using pandas DataFrame operations.
    
    Args:
        weather_data: List of weather data dictionaries
        filters: Dictionary of filters to apply
                Example: {
                    'temperature_2m': {'min': 70, 'max': 85},
                    'wind_speed_10m': {'max': 15},
                    'hour': {'min': 9, 'max': 15}
                }
    
    Returns:
        Filtered list of weather data dictionaries
    """
    if not weather_data:
        return []
    
    # Convert to DataFrame
    df_data = []
    for item in weather_data:
        df_data.append(item)
    
    df = pd.DataFrame(df_data)
    
    # Apply filters
    for column, conditions in filters.items():
        if column in df.columns:
            if isinstance(conditions, dict):
                if 'min' in conditions:
                    df = df[df[column] >= conditions['min']]
                if 'max' in conditions:
                    df = df[df[column] <= conditions['max']]
                if 'equals' in conditions:
                    df = df[df[column] == conditions['equals']]
                if 'contains' in conditions:
                    df = df[df[column].str.contains(conditions['contains'], na=False)]
            else:
                # Simple equality filter
                df = df[df[column] == conditions]
    
    # Convert back to original format
    filtered_data = []
    for _, row in df.iterrows():
        row_dict = row.to_dict()
        filtered_data.append(row_dict)
    
    return filtered_data

def get_weather_filtered(location: str, state: str, forecast_days: int = 1, filters = None) -> List[Dict]:
    print("====filters=====")
    new_filters = {}
    if filters:
        for key, value in filters.items():
            new_filters[key] = {}
            for k, v in value.items():
                new_filters[key][k] = v
        print(new_filters)
    else:
        print("  No filters provided")
    print("====filters=====")
    """
    Get weather data and filter it using pandas operations.
    
    Args:
        location: City name
        state: State name
        forecast_days: Number of days to forecast
        start_hour: Start hour for filtering (0-23)
        end_hour: End hour for filtering (0-23)
        filters: Dictionary of filters to apply
    
    Returns:
        Filtered weather data
    """
    data = get_hourly_forecast(location, state, forecast_days)
    
    if data is None:
        return f"Sorry, an error occurred in get_weather_filtered_pandas: {data}"
    
    if type(data) == str:
        return data

    if new_filters:
        print("Filtering....")
        filtered_data = filter_weather_data_pandas(data, new_filters)
        if len(filtered_data) == 0:
            return f"Sorry, no data found for {location.capitalize()} in {state} with the given filters."
        else:
            print("-----FILTERED DATA-----")
            print(json.dumps(filtered_data))
            print("----filtered data----")
            return filtered_data
    
    return data
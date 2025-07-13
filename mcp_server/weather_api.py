"""
pip install openmeteo-requests pandas requests-cache retry-requests requests tabulate
"""

import json
import pandas as pd
import numpy as np
import re
import requests_cache
import requests
from retry_requests import retry

import openmeteo_requests


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



def get_hourly_forecast(location: str, state: str, forecast_days = 1, latitude: float = None, longitude: float = None, filter_query:str = None, new_columns:list = [], columns_to_show:list = []):
    """
    Default unit is fahrenheit because US is only supported.

    RETURNS data in json format.
    """

    try:
        print("!!!!!!!Get Hourly Forecast!!!!!!!")
        print(location, state, int(forecast_days))

        if latitude is None or longitude is None:
            coordinates = get_coordinates(location, state)
            print(coordinates)
            if coordinates is None:
                return {"error": "No coordinates found for " + location + ", " + state}
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

        def clean_formula(formula_str, df_name="hourly_dataframe"):
            """
            Cleans formulas by:
            1. Removing explicit DataFrame references like 'df['col']' and leaving just 'col'
            2. Converting logical operators to bitwise operators for pandas compatibility
            This is necessary for df.eval() to work correctly.
            """
            # Convert logical operators to bitwise operators for pandas compatibility
            cleaned = formula_str.replace("AND", "&").replace("OR", "|").replace(" and ", " & ").replace(" or ", " | ")
            
            # Regex to find df['col'] or df["col"] and replace it with just col
            pattern = re.compile(rf"{df_name}\s*\[\s*['\"]([^'\"\]]+)['\"]\s*\]")
            return pattern.sub(r'\1', cleaned)


        if filter_query and filter_query != "":
            print("\n\n\nFILTER QUERY\n\n\n")
            print(filter_query)
            filter_query = clean_formula(filter_query)
            print("\n\n\nFILTER QUERY\n\n\n")
            if "pd." in filter_query:
                # Use eval() with pandas in scope for queries with pd references
                scope = {
                    'pd': pd,
                    'np': np,
                    **{col: hourly_dataframe[col] for col in hourly_dataframe.columns}
                }
                mask = eval(filter_query, scope)
                hourly_dataframe = hourly_dataframe[mask]
            else:
                # Use regular query() for simple conditions
                hourly_dataframe = hourly_dataframe.query(filter_query)
            print("FINSIHED FILTERING")
        
        def apply_combined_string_cases(df, plan):
            """
            Correctly applies a 'combined_string' plan to a DataFrame,
            handling exclusive and default cases.
            """
            scope = {
                'pd': pd,
                'np': np,
                **{col: df[col] for col in df.columns}
            }

            # --- Handle Exclusive Cases First ---
            exclusive_case = next((case for case in plan['cases'] if case.get('exclusive')), None)
            if exclusive_case:
                exec(f"exclusive_condition_met = {clean_formula(exclusive_case['condition'])}", scope)
                exclusive_condition_met = scope['exclusive_condition_met']
            else:
                exclusive_condition_met = pd.Series([False] * len(df), index=df.index)

            # --- Handle Regular, Combinable Cases ---
            string_parts_for_cases = []
            regular_cases = [case for case in plan['cases'] if not case.get('exclusive')]
            for case in regular_cases:
                exec(f"condition_met = {clean_formula(case['condition'])}", scope)
                condition_met = scope['condition_met']
                string_parts_for_cases.append(np.where(condition_met, case['value'], ''))

            # Zip and join the parts for each row
            separator = plan.get('separator', ', ')
            joined_rows = [separator.join(filter(None, parts)) for parts in zip(*string_parts_for_cases)]

            # Apply the default value if no regular conditions were met
            default_value = plan.get('default', '')
            combined_results = pd.Series([s if s else default_value for s in joined_rows], index=df.index)

            # --- Final Logic: Prioritize the exclusive value ---
            # If the exclusive condition was met, use its value, otherwise use the combined string.
            final_column = np.where(exclusive_condition_met, exclusive_case['value'], combined_results)

            return final_column
        
        if new_columns and len(new_columns) > 0:
            for new_column in new_columns:
                try:
                    column_name = new_column.get("name")
                    print("Trying to create column: ", column_name)

                    if new_column.get("type") and new_column.get("type") == "combined_string":
                        hourly_dataframe[column_name] = apply_combined_string_cases(hourly_dataframe, new_column)
                    else:
                        formula = new_column.get("formula")
                        # Step 1: Clean the formula to remove explicit dataframe references.
                        cleaned_formula = clean_formula(formula).strip()
                        print(f"  - Cleaned Formula: {cleaned_formula}")

                        # Step 2: Prepare the execution scope.
                        # It includes numpy and all existing columns from the dataframe.
                        # This ensures that when the formula runs, it can find 'np', 'hour_24', 'sunny_percent', etc.
                        scope = {
                            'pd': pd,
                            'np': np,
                            **{col: hourly_dataframe[col] for col in hourly_dataframe.columns}
                        }
                        
                        # Step 3: Execute the formula within the controlled scope.
                        # The result of the formula is assigned to a 'result' variable inside the scope dict.
                        exec(f"result = {cleaned_formula}", scope)
                        
                        # Step 4: Extract the result and assign it to the new column.
                        result = scope['result']
                        hourly_dataframe[column_name] = result
                        
                        print(f"  - SUCCESS: Column '{column_name}' was created.")
                        print("  - DataFrame columns are now:", list(hourly_dataframe.columns))
                except Exception as e:
                    print(f"Error creating column {column_name}: {e}")
                    # Continue with other columns
        
        if columns_to_show and len(columns_to_show) > 0:
            print("\n\n\nCOLUMNS TO SHOW\n\n\n")
            print(columns_to_show)
            # Convert protobuf RepeatedComposite to regular Python list
            hourly_dataframe = hourly_dataframe[list(columns_to_show)]
            print("\n\n\nCOLUMNS TO SHOW\n\n\n")
        
        print(hourly_dataframe.to_markdown())

        """
        hourly_dataframe looks like this:
        {
            "data": {
                "0": 1827519257,
                "1": 1827522857,
                ...
            }, 
            "temperature_2m_fahrenheit": {
                "0": 80,
                "1": 79,
                ...
            },
            ...
        }
        """

        # Convert timestamp to string before converting to dict
        # if "date" in hourly_dataframe.columns or "Date" in hourly_dataframe.columns:
            # hourly_dataframe['date'] = hourly_dataframe['date'].dt.strftime('%Y-%m-%d %H')
        
        print("lkjasdlkajsdf---04092893459384534852========")
        
        # creates an array of dictionaries where each dictionary is a row of the dataframe
        hourly_dataframe = hourly_dataframe.to_dict(orient='records')

        # go through each item in the dataframe and if the values are Timestamp, convert to string
        for item in hourly_dataframe:
            for key, value in item.items():
                if isinstance(value, pd.Timestamp):
                    item[key] = value.strftime('%Y-%m-%d %H')

        print("\n\nHOURLY DATAFRAME\n\n")
        print(hourly_dataframe)
        print("\n\nJSON DUMP\n\n")
        print(json.dumps(hourly_dataframe))

        return {
            "data": json.dumps(hourly_dataframe),
        }

        return json.dumps(hourly_dataframe)

        print("==========OPEN METEO DATA =============")
        print(json.dumps(hourly_dataframe.to_markdown()))
        print(hourly_dataframe.to_json())
        print("=======================")
        return hourly_dataframe.to_markdown()
    except Exception as e:
        print(e)
        return {
            "error": str(e)
        }

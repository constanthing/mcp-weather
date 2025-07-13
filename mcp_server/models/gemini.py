"""
pip install google-generativeai
"""
from os import getenv

from google.generativeai.types import FunctionDeclaration, Tool, GenerationConfig
import google.generativeai as genai

from utils import god_prompt

GEMINI_API_KEY = getenv("GEMINI_API_KEY", None)

if GEMINI_API_KEY is None:
    raise ValueError("API key is required")

# configure genai
genai.configure(api_key=GEMINI_API_KEY)

# define functions the model can call
get_weather_func = FunctionDeclaration(
    name="get_hourly_forecast",
    description="""
    Get the hourly forecast in a given location.
    IMPORTANT: Convert state to full name if it is abbreviated. For example FL to Florida.
    """,
    parameters={
        "type": "OBJECT",
        "properties": {
            "location": {"type": "STRING", "description": "The city name, e.g. San Francisco"},
            "state": {"type": "STRING", "description": "State of the location, e.g. Florida (if abbreviated e.g. FL convert to full name e.g. Florida)"},
            "forecast_days": {
                "type": "NUMBER",
                "description": "Days to forecast. Default is 1 day. Maximum is 16 days."
            },
            "latitude": {
                "type": "NUMBER",
                "description": "Latitude of location. If not provided server will make a request to get the coordinates from the location and state."
            },
            "longitude": {
                "type": "NUMBER",
                "description": "Longitude of location. If not provided server will make a request to get the coordinates from the location and state."
            }, 
        },
        "required": ["location", "state"]
    }
)
get_location_coordinates_func = FunctionDeclaration(
    name="get_coordinates_of_location",
    description="Get the longitude and latitude of a given location.",
    parameters={
        "type": "OBJECT",
        "properties": {
            "location": {"type": "STRING", "description": "The city name, e.g. Labelle"},
            "state": {"type": "STRING", "description": "State of the location, e.g. Florida (if abbreviated e.g. FL convert to full name e.g. Florida)"},
        },
        "required": ["location", "state"]
    }
)


def gemini_get_sql_filter_query(prompt, model="gemini-2.5-flash"):
    model = genai.GenerativeModel(
        model_name=model,
        system_instruction=god_prompt,
        generation_config=GenerationConfig(
            temperature=0.0,
            top_p=0.0,
            max_output_tokens=30000,
            response_mime_type="application/json"
        )
    )

    chat_session = model.start_chat()

    response = chat_session.send_message(prompt)

    try:
        if response.text == "":
            return None
    except Exception as e:
        return None

    return response.text
"""
pip3 install cerebras_cloud_sdk
"""
import json
from time import time

from cerebras.cloud.sdk import Cerebras

from .weather_api import get_hourly_forecast

# api_key = "csk-4tteyn5d9tjxcyc3hpfnwwftpmcdccykkmk966der4vxx23c"
api_key = "csk-f4kxpnyncrkt6nf59tfdtde6kfywtyhdedy548txmphth29n"

client = Cerebras(api_key=api_key)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_hourly_forecast",
            "strict": True,
            "description": """
                Get the hourly forecast in a given location.
                Returns an array of dictionaries where index values start from today and end at the end of the forecast days.
                Data points returned are:
                - temperature
                - precipitation probability
                - relative humidity
                - cloud cover
                - wind speed
                - wind gusts
                - apparent temperature
                - date

                If hour is in 12 hour format convert to 24 hour format. For example 5 pm is 17.
            """,
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "The city name, e.g. San Francisco"},
                    "state": {"type": "string", "description": "State of the location, e.g. Florida (if abbreviated e.g. FL convert to full name e.g. Florida)"},
                    "forecast_days": {
                        "type": "number",
                "description": "Days to forecast. Default is 1 day. Maximum is 16 days."
                    },
                    "latitude": {
                        "type": "number",
                        "description": "Latitude of location. If not provided server will make a request to get the coordinates from the location and state."
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude of location. If not provided server will make a request to get the coordinates from the location and state."
                    }, 
                    "start_hour": {
                        "type": "number",
                        "description": "Start hour of the day to forecast in 24 hour format. Default is 0. Maximum is 23."
                    },
                    "end_hour": {
                        "type": "number",
                        "description": "End hour of the day to forecast in 24 hour format. Default is 0. Maximum is 23."
                    },
                },
                "required": ["location", "state"]
            }
        }
    }
]



def get_response(messages:list, user_input:str, model_name:str = "llama3.1-8b") -> dict:
    # add user message to chat history
    messages.append({"role": "user", "content": user_input})

    # Register every callable tool once
    available_functions = {
        "get_hourly_forecast": get_hourly_forecast,
    }

    text = None
    model_response_time = None
    function_response_id = None

    model_response_time = time()

    while True:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=tools,
            parallel_tool_calls=False
        )

        msg = response.choices[0].message

        # If the assistant didn’t ask for a tool, we’re done
        if not msg.tool_calls:
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": msg.tool_calls,
            })
            text = msg.content
            break

        # Save the assistant turn exactly as returned
        print(msg.model_dump())
        messages.append(msg.model_dump())    

        # Run the requested tool
        call  = msg.tool_calls[0]
        fname = call.function.name

        if fname not in available_functions:
            raise ValueError(f"Unknown tool requested: {fname!r}")

        args_dict = json.loads(call.function.arguments)  # assumes JSON object
        output = available_functions[fname](**args_dict)

        # Feed the tool result back
        messages.append({
            "role": "tool",
            "tool_name": fname,
            "content": json.dumps(output),
            "tool_call_id": call.id,
        })
        function_response_id = call.id
    
    model_response_time = round(time() - model_response_time, 2)

    return {
        "text": text,
        "history": messages,
        "model_response_time": model_response_time,
        "function_response_id": function_response_id,
    }
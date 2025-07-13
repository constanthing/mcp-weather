"""
pip3 install cerebras_cloud_sdk
"""
import json
from time import time

from cerebras.cloud.sdk import Cerebras

from .weather_api import get_hourly_forecast, get_weather_filtered
from .utils import _make_serializable, get_html_table


# api_key = "csk-4tteyn5d9tjxcyc3hpfnwwftpmcdccykkmk966der4vxx23c"
api_key = "csk-f4kxpnyncrkt6nf59tfdtde6kfywtyhdedy548txmphth29n"

client = Cerebras(api_key=api_key)

tools_map = {
    "get_hourly_forecast": get_hourly_forecast,
    # "get_weather_filtered": get_weather_filtered,
    # "get_html_table_from_data": get_html_table
}

# Raw dictionary definition of parameters
tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "get_hourly_forecast",
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
    },
   
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "get_html_table_from_data",
    #         "description": """
    #             Converts data from any of the tools into an HTML table.

    #             The data paremeter must be the exact, unmodified output from any weather tool.
    #             Do not change, reformat, or process this data in any way before passing it.
    #             The weather tools already return data in the correct format required.

    #             Data must be in this format [{"key1": value1, "key2": value2, "key3": value3}, ...]

    #             Custom columns are supported. So long as the custom_columns are in the format [{"column_name": [value1, value2, value3]}, ...]
    #         """,
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "tool_call_id": {
    #                     "type": "string",
    #                     "description": "The id of a tool call id (e.g. call_75140928) that returned the data to be converted into an HTML table."
    #                 },
    #                 "custom_columns": {
    #                     "type": "array",
    #                     "description": "Custom columns to add to the HTML table. Must be in the format [{'column_name': [value1, value2, value3...]}, ...]. This is an array. Default is empty array."
    #                 }
    #             },
    #             "required": ["data"]
    #         }
    #     }
    # },
]


def get_response(messages:list, message:str, model_name:str = "llama3.1-8b") -> dict:
    try:
        # add user message to messages
        messages.append({
            "role": "user",
            "content": message
        })

        model_response_time = time()
        # TODO!: 
        function_call_responses = {}

        yield json.dumps({
            "text": "Sending user prompt to model"
        }) + "[DELIMITER]"

        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            tools=tools_definition,  # The dictionary of our functions and their parameters
            parallel_tool_calls=False,
            temperature=0.2
        )

        function_responses = {}

        function_call_id = None

        # check if function call in response body
        while True:
            print("==========TOOL CALLS==========")
            print(response.choices[0].message.tool_calls)
            print("==========TOOL CALLS==========")
            if response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:

                    yield json.dumps({
                        "text": "🔨 Calling tool " + tool_call.function.name
                    }) + "[DELIMITER]"

                    # Get the tool function name and arguments Cerebras wants to call
                    function_name = tool_call.function.name
                    if function_name not in tools_map:
                        messages.append({
                                "role": "tool",
                                "content": json.dumps({"error": f"Function {function_name} not found"}),
                                "tool_call_id": tool_call.id
                            })
                        continue
                    function_args = json.loads(tool_call.function.arguments)

                    # Call one of the tool function defined earlier with arguments
                    result = tools_map[function_name](**function_args)

                    print("==========RESULT==========")
                    print(tool_call)

                    yield json.dumps({
                        'status': 'tool',
                        'data': result
                    }) + "[DELIMITER]"

                    # Append the result from tool function call to the chat message history,
                    # with "role": "tool"
                    messages.append(
                        {
                            "role": "tool",
                            "tool_name": function_name,
                            "content": json.dumps(result),
                            "tool_call_id": tool_call.id  # tool_call.id supplied in Cerebras's response
                        }
                    )
                
                yield json.dumps({
                    "text": "Model analyzing tool call results..."
                }) + "[DELIMITER]"
            
                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=messages,
                        tools=tools_definition,
                        parallel_tool_calls=False
                    )
                    print("END OF LOOP")
                except Exception as e:
                    print("ERROR")
                    print(e)
                    return e
            else:
                break
        
        print("BREAKED")

        # Check if content exists before accessing it
        content = response.choices[0].message.content or ""
        
        messages.append({
            "role": "assistant",
            "content": content
        })

        model_response_time = round(time() - model_response_time, 2)

        reply = content

        yield {
            "status": "response",
            "text": reply,
            "history": messages,
            "model_response_time": model_response_time,
            "function_response_id": function_call_id,
        }
    except Exception as e:
        yield json.dumps({
            "status": "error",
            "error": f"Something went wrong: {e}"
        }) + "[DELIMITER]" 
        return e 
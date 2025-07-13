"""
pip3 install openai
"""
import json
from time import time

from openai import OpenAI

from .weather_api import get_hourly_forecast, get_weather_filtered
from .utils import _make_serializable, get_html_table
from .models import FunctionResponse


api_key = "xai-aJPB7yfiMFs9yeEpj3P7DvmRdWHDcQYEhJnWE6U46sCS1OtabQ6Dj6YMGbF8RKP4vKBpkFiFRsqHINKh"


client = OpenAI(
    api_key=api_key,
    base_url="https://api.x.ai/v1",
)



# Raw dictionary definition of parameters
tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "get_hourly_forecast",
            "description": """
                Get the hourly forecast in a given location.
                Returns data in json format.
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
    #         "name": "get_weather_filtered",
    #         "description": """
    #             Get the weather data for a given location and filters it based on the provided filters.
    #             Keys to filter on are:
    #             - temperature_2m
    #             - precipitation_probability
    #             - relative_humidity_2m
    #             - cloud_cover
    #             - wind_speed_10m
    #             - wind_gusts_10m
    #             - apparent_temperature
    #             - hour (24 hour format) 
    #         """,
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "location": {"type": "string", "description": "The city name, e.g. San Francisco"},
    #                 "state": {"type": "string", "description": "State of the location, e.g. Florida (if abbreviated e.g. FL convert to full name e.g. Florida)"},
    #                 "forecast_days": {
    #                     "type": "number",
    #                     "description": "Days to forecast. Default is 1 day. Maximum is 16 days."
    #                 },
    #                 "filters": {
    #                     "type": "object",
    #                     "description": "Filters to apply to the weather data. Keys are the column names in the weather data. Values are the filters to apply to the column. Available filters: min, max, equals, contains.",
    #                 }
    #             },
    #             "required": ["location", "state", "forecast_days", "filters"]
    #         }
    #     }
    # },
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


def modify_data(modification_prompt: str, data: str):
    # TODO!: add chunking
    # TODO!: add parallel processing

    data = json.loads(data)

    response = client.chat.completions.create(
        model="grok-3-fast",
        messages=[
            {
                "role": "system",
                "content": """
                You are a JSON data modification assistant (post-processor).
                The data you are given is in this format: [{"key1": value1, "key2": value2, "key3": value3}, ...]
                Your job is to apply this prompt on the provided data. 
                """ + """\n
                Prompt: {modification_prompt}
                """
            },
            {
                "role": "user",
                "content": data
            }
        ],
        max_tokens=8000,
        temperature=0.0
    )
    print("==========MODIFY DATA==========")
    print(response.choices[0].message.content)
    return response.choices[0].message.content


def get_markdown_table(function_response_id: str):
    data = FunctionResponse.objects.get(id=function_response_id).response
    if not data:
        return "Error: Function response not found for id: " + function_response_id 
    
    data = json.loads(data)

    headers = data[0].keys()
    header_row = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    rows = ["| " + " | ".join(str(row[h]) for h in headers) + " |" for row in data]

    return "\n".join([header_row, separator] + rows)


tools_map = {
    "get_hourly_forecast": get_hourly_forecast,
    "modify_data": modify_data,
    "get_markdown_table": get_markdown_table,
    # "get_weather_filtered": get_weather_filtered,
    # "get_html_table_from_data": get_html_table
}

def get_response(messages:list, message:str, model_name:str = "grok-3-latest") -> dict:
    try:
        # add user message to messages
        messages.append({
            "role": "user",
            "content": message
        })

        model_response_time = time()

        yield json.dumps({
            "text": "Sending user prompt to model"
        }) + "[DELIMITER]"

        response = client.chat.completions.create(
            model="grok-3-fast",
            messages=messages,
            tools=tools_definition,  # The dictionary of our functions and their parameters
            tool_choice="auto",
            max_tokens=30000,
            temperature=0.0
        )

        function_response_id = None

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

                    # Get the tool function name and arguments Grok wants to call
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

                    yield json.dumps({
                        'status': 'tool',
                        'data': result
                    }) + "[DELIMITER]"

                    # Append the result from tool function call to the chat message history,
                    # with "role": "tool"
                    temp = {
                        "role": "tool",
                        "tool_name": function_name,
                        "content": result,
                        "tool_call_id": tool_call.id  # tool_call.id supplied in Grok's response
                    }
                    print(temp)
                    messages.append(temp)
                
                yield json.dumps({
                    "text": "Model analyzing tool call results..."
                }) + "[DELIMITER]"
            
                response = client.chat.completions.create(
                    model="grok-3-fast",
                    messages=messages,
                    tools=tools_definition,
                    tool_choice="auto",
                    max_tokens=30000,
                    temperature=0.0
                )
            else:
                break

            print(response.choices[0].message)
            print(response.choices[0])

        messages.append({
            "role": "assistant",
            "content": response.choices[0].message.content
        })

        model_response_time = round(time() - model_response_time, 2)

        reply = response.choices[0].message.content

        yield {
            "status": "response",
            "text": reply,
            "history": messages,
            "model_response_time": model_response_time,
            "function_response_id": function_response_id,
        }
    except Exception as e:
        yield json.dumps({
            "status": "error",
            "error": f"Something went wrong: {e}"
        }) + "[DELIMITER]"
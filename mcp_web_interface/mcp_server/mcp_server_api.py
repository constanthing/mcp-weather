from time import time
import json
from io import StringIO
import pandas as pd

import requests

import traceback

def get_mcp_server_response(user_input:str, model_name:str) -> dict:
    url = "http://localhost:8080/weather/data"
    model_response = None

    try:
        response = requests.post(url, json={"prompt": user_input, "model": model_name})
        print(response)
        response = response.json()
        data = response["data"]
        mcp_server_response_time = response["model_execution_time"]
        if "data" in response and data is not None:
            model_response = pd.read_json(StringIO(data))
            model_response = model_response.to_html(border=0)
            yield {
                "status": "response",
                "text": model_response,
                "model_response_time": response.get("model_execution_time"),
                "function_response_time": response.get("function_execution_time"),
                "function_name": response.get("function_name"),
                "function_args": response.get("function_args"),
            }
        else:
            yield {
                "status": "error",
                "error": response["error"]
            }
    except Exception as e:
        yield {
            "status": "error",
            "error": f"Something went wrong: {e}"
        }

    

def get_mcp_server_response_stream(user_input:str, model_name:str) -> dict:
    try:
        url = "http://localhost:8080/weather/data/stream"
        headers = {
            "Content-Type": "application/json",
        }
        response = requests.post(url, json={"prompt": user_input, "model": model_name}, headers=headers, stream=True)
        if response.status_code != 200:
            yield {
                "status": "error",
                "error": f"Something went wrong: {response.status_code}"
            }
        
        start_time = time()
        for line in response.iter_lines():
            if line:
                line_str = line.decode("utf-8").strip()
                if line_str:
                    print(f"[{time() - start_time:.2f}s] Message: {line_str}")
                    event_data = json.loads(line_str)
                    message = event_data.get("message") 
                    result = event_data.get("result")
                    error = event_data.get("error")

                    if message:
                        print("message: ", message)
                        yield json.dumps({
                            "text": message
                        }) + "[DELIMITER]"
                    elif result:
                        print("result: ", result)
                        if "data" in result and result.get("data") is not None:
                            # convert json from mcp server to html table
                            model_response = pd.read_json(StringIO(result.get("data"))).to_html()
                        else:
                            model_response = "No data key from mcp server"
                        yield {
                            "status": "response",
                            "text": model_response,
                            "model_response_time": result.get("model_execution_time"),
                            "function_response_time": result.get("function_execution_time"),
                            "function_name": result.get("function_name"),
                            "function_args": result.get("function_args"),
                        }
                    elif error:
                        yield {
                            "status": "error",
                            "error": error
                        }
    except Exception as e:
        print(e)
        yield {
            "status": "error",
            "error": f"Something went wrong: {traceback.format_exc()}"
        }
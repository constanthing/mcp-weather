"""
pip install fastapi
pip install uvicorn
pip install pandas
"""
# standard imports
import json
import time
import asyncio
from datetime import datetime

# external imports
from fastapi import FastAPI, Depends, HTTPException, Request as FastAPIRequest
from fastapi.responses import StreamingResponse
import uvicorn

# local imports
from schemas import Request, WeatherData

from weather_api import get_hourly_forecast, get_coordinates

from utils import extract_json_from_code_block

from google.generativeai.types import FunctionDeclaration, Tool, GenerationConfig
from models.gemini import genai, gemini_get_sql_filter_query, get_weather_func, get_location_coordinates_func
from models.cerebras import cerebras_get_sql_filter_query
from models.openai import openai_get_sql_filter_query

app = FastAPI(title="MCP Weather API")


available_tools = {
    "get_hourly_forecast": get_hourly_forecast,
    "get_coordinates_of_location": get_coordinates,
}


def get_sql_filter_query(prompt, model="gemini-2.5-flash"):
    if "gemini" in model:
      response = gemini_get_sql_filter_query(prompt, model)
    elif "qwen" in model:
      print("\n\nCerebras")
      response = cerebras_get_sql_filter_query(prompt, model)
    elif "gpt" in model:
      response = openai_get_sql_filter_query(prompt, model)
    else:
      raise ValueError(f"Model {model} not supported")

    print(response)

    return response


@app.post("/weather/data")
def get_weather_data(request: Request):
    final_response = {
      "data": None
    }

    # this model is very fast (~1 sec avg.) no need to use Cerebras or OpenAI
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        tools=Tool(function_declarations=[get_weather_func, get_location_coordinates_func]),
        system_instruction=(f"""
        You are a weather assistant.
        Your main task is to call tools to get the weather data.
        Ignore any filtering, modification, or transformation instructions.
        If prompt is asking for weather data, run the tool for the job. Ignore any other instructions.
        You are to not converse with the user. You are to only call tools to get the weather data.
        Extract the location, state, and forecast days from the prompt. Optionally you can also extract the longitude and latitude. That is all you need to do.

        Today is {datetime.now().strftime("%Y-%m-%d")}
        """),
        generation_config=GenerationConfig(
            temperature=0.0,
            top_p=0.0,
            max_output_tokens=512
        )
    )

    chat_session = model.start_chat()

    model_execution_time = time.time()
    response = chat_session.send_message(request.prompt)

    if response.candidates[0].content.parts:
      function_call = response.candidates[0].content.parts[0].function_call
    else:
      function_call = None

    if function_call and function_call.name == "get_hourly_forecast":
        function_name = function_call.name
        # Convert MapComposite to regular Python dict
        function_args = dict(function_call.args)

        if function_name not in available_tools:
            raise HTTPException(status_code=400, detail=f"Function {function_name} not found")

        try:
            filter_query = json.loads(extract_json_from_code_block(get_sql_filter_query(request.prompt, request.model)))
            print(filter_query)
            
            # Create a new dict with all the arguments
            final_args = dict(function_args)
            final_args["filter_query"] = filter_query.get("filter_condition")
            
            # Convert protobuf objects to regular Python types
            new_columns_raw = filter_query.get("new_columns")
            if new_columns_raw:
                final_args["new_columns"] = [dict(item) for item in new_columns_raw]
            else:
                final_args["new_columns"] = []
            
            columns_to_show_raw = filter_query.get("columns_to_show")
            if columns_to_show_raw:
                final_args["columns_to_show"] = list(columns_to_show_raw)
            else:
                final_args["columns_to_show"] = []
                
            # Use the final_args instead of function_args
            function_args = final_args
        except Exception as e:
            return {
                "error": f"Something went wrong: {e}. Please try again."
            }
        
        function_execution_time = time.time()
        function_result = available_tools[function_name](**function_args)
        function_execution_time = time.time() - function_execution_time

        if function_result.get("error"):
            raise HTTPException(status_code=400, detail=function_result.get("error"))

        print(function_result)

        if function_result is None:
            raise HTTPException(status_code=400, detail="Function returned None")


        final_response["data"] = function_result.get("data")

        print("\n\nFINAL RESPONSE\n\n")

        final_response["function_execution_time"] = function_execution_time

        print("\n\nFINAL EXECUTION TIME\n\n")

        final_response["function_name"] = function_name

        print("\n\nFUNCTION ARGS\n\n")

        final_response["function_args"] = function_args

        print("\n\nMODEL EXECUTION TIME\n\n")

    else:
        final_response["error"] = response.candidates[0].content.parts[0].text 

    print("lkajsdflkajf")
    final_response["model_execution_time"] = time.time() - model_execution_time
    print("YES")

    print(final_response)

    return final_response


@app.post("/weather/data/stream")
async def get_weather_data_stream(request: Request):
    """
    Streaming version of weather data endpoint that provides real-time updates
    """
    
    async def generate_stream():
        final_response = {
            "data": None,
            "function_execution_time": None,
            "function_name": None,
            "function_args": None,
            "model_execution_time": None
        }

        # Step 1: Start processing
        yield f"{json.dumps({'message': 'Processing weather request...'})}\n"
        await asyncio.sleep(0.1)  # Force immediate flush
        
        # Step 2: Initialize model
        yield f"{json.dumps({'message': 'Initializing AI model...'})}\n"
        await asyncio.sleep(0.1)  # Force immediate flush
        
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            tools=Tool(function_declarations=[get_weather_func, get_location_coordinates_func]),
            system_instruction=("""
            You are a weather assistant.
            Your main task is to call tools to get the weather data.
            Ignore any filtering, modification, or transformation instructions.
            If prompt is asking for weather data, run the tool for the job. Ignore any other instructions.
            You are to not converse with the user. You are to only call tools to get the weather data.
            Extract the location, state, and forecast days from the prompt. Optionally you can also extract the longitude and latitude. That is all you need to do.
            """),
            generation_config=GenerationConfig(
                temperature=0.0,
                top_p=0.0,
                max_output_tokens=512
            )
        )

        chat_session = model.start_chat()
        
                # Step 3: Send message to model
        yield f"{json.dumps({'message': 'Analyzing request with AI...'})}\n"
        await asyncio.sleep(0.1)  # Force immediate flush
        
        model_execution_time = time.time()
        response = chat_session.send_message(request.prompt)
        
        print(response)
        
        # Step 4: Model response received
        yield f"{json.dumps({'message': 'AI analysis complete', 'model_time': time.time() - model_execution_time})}\n"
        await asyncio.sleep(0.1)  # Force immediate flush

        if response.candidates[0].content.parts:
            function_call = response.candidates[0].content.parts[0].function_call
        else:
            function_call = None

        if function_call and function_call.name == "get_hourly_forecast":
            function_name = function_call.name
            function_args = dict(function_call.args)
            
            # Step 5: Processing filter query
            yield f"{json.dumps({'message': 'Processing filter query...'})}\n"
            await asyncio.sleep(0.05)  # Force immediate flush
            
            try:
                filter_query = json.loads(extract_json_from_code_block(get_sql_filter_query(request.prompt, request.model)))
                
                final_args = dict(function_args)
                final_args["filter_query"] = filter_query.get("filter_condition")
                
                new_columns_raw = filter_query.get("new_columns")
                if new_columns_raw:
                    final_args["new_columns"] = [dict(item) for item in new_columns_raw]
                else:
                    final_args["new_columns"] = []
                
                columns_to_show_raw = filter_query.get("columns_to_show")
                if columns_to_show_raw:
                    final_args["columns_to_show"] = list(columns_to_show_raw)
                else:
                    final_args["columns_to_show"] = []
                    
                function_args = final_args
                
                yield f"{json.dumps({'message': 'Filter processing complete'})}\n"
                await asyncio.sleep(0.1)  # Force immediate flush
                
            except Exception as e:
                yield f"{json.dumps({'error': f'Filter processing failed: {e}'})}\n"
                return
            
            # Step 6: Getting weather data
            yield f"{json.dumps({'message': 'Fetching weather data from API...'})}\n"
            await asyncio.sleep(0.1)  # Force immediate flush
            
            function_execution_time = time.time()
            function_result = available_tools[function_name](**function_args)
            function_execution_time = time.time() - function_execution_time

            if function_result.get("error"):
                # yield f"{json.dumps({'error': function_result.get('error')})}\n"
                return

            # Step 7: Update final_response with actual results
            final_response.update({
                "data": function_result.get("data"),
                "function_execution_time": round(function_execution_time, 2),
                "function_name": function_name,
                "function_args": function_args,
                "model_execution_time": round(time.time() - model_execution_time, 2)
            })
            
            yield f"{json.dumps({'result': final_response})}\n"
            
        else:
            yield f"{json.dumps({'error': 'No weather function called'})}\n"
            return

    return StreamingResponse(
        generate_stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "application/x-ndjson",
            "X-Accel-Buffering": "no"  # Disable nginx buffering if using nginx
        }
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
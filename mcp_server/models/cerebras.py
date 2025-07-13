"""
pip install cerebras_cloud_sdk
"""
from os import getenv

from cerebras.cloud.sdk import Cerebras

from utils import god_prompt

CEREBRAS_API_KEY = getenv("CEREBRAS_API_KEY", None)

if CEREBRAS_API_KEY is None:
    raise ValueError("API key is required")

client = Cerebras(
    api_key=CEREBRAS_API_KEY
)

def cerebras_get_sql_filter_query(prompt, model="qwen-3-32b"):
    """
    Available models:
    - qwen-3-32b (16k context window)
    - llama3.1-8b (8k context window)
    - llama-3.3-70b (8k context window)
    """
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": god_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            tools=None,
            model=model,
            stream=False,
            max_completion_tokens=16382,
            temperature=0.1,
            top_p=0.0,
            # json_object ensures the response is either valid JSON or or error response without enforcing a specific schema format 
            # json is not compatible with streaming (stream must be set to false)
        )
        print(response.usage.total_tokens)
        print(response.choices)
        return response.choices[0].message.content.replace("<think>", "").replace("</think>", "")
    except Exception as e:
        print(e)
        return None
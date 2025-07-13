"""
pip install openai
"""

from openai import OpenAI

from utils import god_prompt

# automatically reads the OPENAI_API_KEY from the environment variables

client = OpenAI()

def openai_get_sql_filter_query(prompt, model="gpt-4.1-mini"):
    print("lkjasdlkjaslkdfj")
    print(model)
    try:
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": god_prompt
                        }
                    ]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt
                        }
                    ]
                }
            ],
            temperature=0.0,
            store=False,
            tools=[],
            reasoning={},
            max_output_tokens=6000
        )
    except Exception as e:
        print(e)
        return None
    print(response)
    print(response.output[0].content[0].text)
    return response.output[0].content[0].text
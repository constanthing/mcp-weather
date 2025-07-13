source venv/bin/activate

export GEMINI_API_KEY= # your key here
export CEREBRAS_API_KEY= # your key here
export OPENAI_API_KEY= # your key here

uvicorn router:app --reload --port 8080
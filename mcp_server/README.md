** Running program
Make sure to have installed all the necessary dependencies first!
`
source setup.sh # make sure to add keys
uvicorn router:app --reload --port 8080
`

** Environment variables
The program checks for these environment variables. At least one is required in order to run. 
- GEMINI_API_KEY 
- CEREBRAS_API_KEY
- OPENAI_API_KEY
*** Quickly adding these keys
Modify env_keys.sh to include your keys then run
`
source env_keys.sh
`

* Weather API Limitations
- Max forecast of 16 days

* TODO
- if user asks for summaries, run process_row() logic, then send results back to the LLM
"Summarize trends from this data."


* Example Prompts
- What is the weather in Lehigh Acres, FL on Tuesday? 
- Show the temperatures 


* Prompts that fail (working on)
- Create a column that shows the average temperature for each day in the next 5 days. 


# Install
`
pip install fastapi uvicorn pandas openmeteo-requests pandas requests-cache retry-requests requests tabulate cerebras_cloud_sdk google-generativeai openai grpcio
`
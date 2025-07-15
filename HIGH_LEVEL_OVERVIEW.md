# Weather MCP Application - Technical Deep Dive

This is a sophisticated weather data analysis platform that combines AI-powered natural language processing with real-time weather data retrieval. The system uses a two-tier architecture with a FastAPI-based MCP (Model Context Protocol) server and a Django web interface.

## 🏗️ High-Level Architecture

The application follows a **two-tier architecture**:

1. **Web Interface Layer** (Django/SQLite): Handles user interactions, chat history, and model management
2. **MCP Server Layer** (FastAPI): Processes weather data and AI model integration

## 🔄 Core Data Flow

```
User Query → Web Interface → MCP Server → AI Model → Function Call → Weather API → Data Processing → Response
```

### Step-by-Step Process:

1. **User Input**: Natural language weather query (e.g., "What's the weather in Miami, FL tomorrow?")
2. **Model Processing**: AI model interprets the query and determines which tools to call
3. **Function Calling**: Model calls appropriate weather functions with extracted parameters
4. **Data Retrieval**: Weather data fetched from Open-Meteo API
5. **Data Processing**: Pandas-based filtering and transformation
6. **Response Generation**: Processed data returned to user

## 🧠 AI Model Integration

The system supports multiple AI models through a unified interface:

### Model Selection Logic (`router.py`)
```python
def get_sql_filter_query(prompt, model="gemini-2.5-flash"):
    if "gemini" in model:
        response = gemini_get_sql_filter_query(prompt, model)
    elif "qwen" in model:
        response = cerebras_get_sql_filter_query(prompt, model)
    elif "gpt" in model:
        response = openai_get_sql_filter_query(prompt, model)
```

### Function Declarations (`models/gemini.py`)
The system defines specific functions that AI models can call:

```python
get_weather_func = FunctionDeclaration(
    name="get_hourly_forecast",
    description="Get the hourly forecast in a given location.",
    parameters={
        "type": "OBJECT",
        "properties": {
            "location": {"type": "STRING"},
            "state": {"type": "STRING"},
            "forecast_days": {"type": "NUMBER"},
            "latitude": {"type": "NUMBER"},
            "longitude": {"type": "NUMBER"}
        },
        "required": ["location", "state"]
    }
)
```

## 🌤️ Weather Data Processing

### Core Weather API (`weather_api.py`)

The `get_hourly_forecast()` function is the heart of the weather processing:

```python
def get_hourly_forecast(location: str, state: str, forecast_days=1, 
                       latitude: float = None, longitude: float = None, 
                       filter_query: str = None, new_columns: list = [], 
                       columns_to_show: list = []):
```

**Key Processing Steps:**

1. **Geocoding**: Converts location names to coordinates using Open-Meteo's geocoding API
2. **Data Retrieval**: Fetches weather data from Open-Meteo with specific parameters:
   - Temperature (Fahrenheit)
   - Precipitation probability
   - Relative humidity
   - Cloud cover
   - Wind speed (MPH)
   - Wind gusts
   - Apparent temperature

3. **DataFrame Creation**: Converts API response to pandas DataFrame with additional time-based columns:
   ```python
   hourly_dataframe['year'] = hourly_dataframe['date'].dt.year
   hourly_dataframe['month'] = hourly_dataframe['date'].dt.month
   hourly_dataframe['day'] = hourly_dataframe['date'].dt.day
   hourly_dataframe['hour_24'] = hourly_dataframe['date'].dt.hour
   hourly_dataframe['day_of_week'] = hourly_dataframe['date'].dt.strftime('%A')
   ```

### Advanced Data Processing

#### Formula Cleaning (`clean_formula()`)
```python
def clean_formula(formula_str, df_name="hourly_dataframe"):
    # Converts logical operators for pandas compatibility
    cleaned = formula_str.replace("AND", "&").replace("OR", "|")
    # Removes explicit DataFrame references
    pattern = re.compile(rf"{df_name}\s*\[\s*['\"]([^'\"\]]+)['\"]\s*\]")
    return pattern.sub(r'\1', cleaned)
```

#### Dynamic Column Creation
The system can create new columns based on AI-generated formulas:

```python
# Example: Creating temperature in Celsius
formula = "(temperature_2m_fahrenheit - 32) * 5 / 9"
exec(f"result = {cleaned_formula}", scope)
hourly_dataframe[column_name] = result
```

#### Combined String Logic
For complex conditional text generation:

```python
def apply_combined_string_cases(df, plan):
    # Handles multiple conditions to create descriptive text
    # Example: "Hot, Humid, Windy" based on temperature, humidity, wind
```

## �� API Endpoints

### MCP Server Endpoints (`router.py`)

**Main Weather Data Endpoint:**
```python
@app.post("/weather/data")
def get_weather_data(request: Request):
```

**Streaming Endpoint:**
```python
@app.post("/weather/data/stream")
async def get_weather_data_stream(request: Request):
```

### Request/Response Flow:

1. **Request Processing**: 
   ```python
   model = genai.GenerativeModel(
       model_name="gemini-2.5-flash",
       tools=Tool(function_declarations=[get_weather_func, get_location_coordinates_func]),
       system_instruction="You are a weather assistant..."
   )
   ```

2. **Function Call Extraction**:
   ```python
   function_call = response.candidates[0].content.parts[0].function_call
   function_args = dict(function_call.args)
   ```

3. **Filter Query Processing**:
   ```python
   filter_query = json.loads(extract_json_from_code_block(
       get_sql_filter_query(request.prompt, request.model)
   ))
   ```

## 🎨 Web Interface Architecture

### Django Views (`views.py`)

**Chat Management:**
```python
def chat(request, chat_id=None):
    if request.method == "GET":
        return get_chat(request, chat_id)
    elif request.method == "POST":
        if not chat_id:
            return create_chat(request)
        else:
            return update_chat(request, chat_id)
```

**Streaming Response:**
```python
def stream_response():
    # Real-time updates during processing
    yield json.dumps({"text": "Processing weather request..."}) + "[DELIMITER]"
```

### MCP Server Integration (`mcp_server_api.py`)

**Standard Request:**
```python
def get_mcp_server_response(user_input: str, model_name: str) -> dict:
    url = "http://localhost:8080/weather/data"
    response = requests.post(url, json={"prompt": user_input, "model": model_name})
```

**Streaming Request:**
```python
def get_mcp_server_response_stream(user_input: str, model_name: str) -> dict:
    url = "http://localhost:8080/weather/data/stream"
    response = requests.post(url, json={"prompt": user_input, "model": model_name}, stream=True)
```

## 📊 Data Models

### Chat Management (`models.py`)

```python
class Chat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    title = models.CharField(max_length=30, default=None, null=True)
    history = models.TextField(default="[]")
    history_full = models.TextField(default="[]")
    created_at = models.DateTimeField(auto_now_add=True)
    model = models.CharField(max_length=255, default="gemini-2.5-flash")
```

## 🔄 Key Processing Routines

### 1. Natural Language to SQL Translation (`utils.py`)

The `god_prompt` contains comprehensive instructions for converting natural language to structured queries:

```python
god_prompt = """
You are an expert AI assistant that translates natural language queries into a structured JSON query plan.

Your response MUST be a JSON object with:
{
  "filter_condition": "SQL WHERE clause string",
  "new_columns": [{"name": "column_name", "formula": "pandas_formula"}],
  "columns_to_show": ["list_of_column_names"]
}
"""
```

### 2. Formula Execution Engine

The system uses a controlled execution environment for dynamic formula evaluation:

```python
scope = {
    'pd': pd,
    'np': np,
    **{col: hourly_dataframe[col] for col in hourly_dataframe.columns}
}
exec(f"result = {cleaned_formula}", scope)
```

### 3. Caching and Performance

**API Caching:**
```python
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
```

**Performance Tracking:**
```python
model_execution_time = time.time()
function_execution_time = time.time()
```

## 🎯 Advanced Features

### 1. Dynamic Data Transformation
- **Column Creation**: Formula-based new columns
- **Filtering**: SQL-like queries on weather data
- **Aggregation**: Statistical analysis capabilities

### 2. Real-time Streaming
- **Progress Updates**: Real-time status during processing
- **Incremental Results**: Stream data as it becomes available

## �� Error Handling and Resilience

### Graceful Degradation
```python
try:
    function_result = available_tools[function_name](**function_args)
except Exception as e:
    return {"error": f"Something went wrong: {e}"}
```

### Retry Logic
```python
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
```

## 🚀 Performance Optimizations

1. **Caching**: 1-hour cache for weather API responses
2. **Model Selection**: Fast models for simple queries, powerful models for complex analysis
3. **Streaming**: Real-time updates reduce perceived latency
4. **Efficient Data Processing**: Pandas-based operations for large datasets

# MCP Weather Application

A comprehensive weather data analysis platform that combines AI-powered natural language processing with real-time weather data retrieval. This application consists of two main components: a FastAPI-based MCP (Model Context Protocol) server for weather data processing and a Django web interface for user interaction.

## 🏗️ Architecture Overview

### Two-Tier Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Interface Layer                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Chat Interface│  │ Custom Prompts  │  │ Model Mgmt  │ │
│  │   (Django)      │  │   Management    │  │   & History │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   MCP Server Layer                         │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   AI Models     │  │  Weather API    │  │ Data Filter │ │
│  │  (Gemini/Cerebras│  │  Integration    │  │ & Processing│ │
│  │   /OpenAI)      │  │  (Open-Meteo)   │  │  (Pandas)   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Core Components

### 1. MCP Server (`mcp_server/`)
**FastAPI-based backend service that handles weather data processing and AI model integration**

- **Weather Data API**: Retrieves real-time weather data from Open-Meteo API
- **AI Model Integration**: Supports multiple AI models for natural language processing
  - Gemini 2.5 Flash/Pro (Google)
  - Cerebras Qwen 3-32B
  - OpenAI GPT-4.1 Mini
- **Data Processing**: Advanced filtering and transformation capabilities using Pandas
- **Function Calling**: AI models can call weather functions to retrieve specific data

**Key Features:**
- Real-time weather data retrieval with caching
- Natural language to SQL-like filtering
- Dynamic column creation and data transformation
- Streaming responses for real-time updates (in progress)
- Multi-model support with automatic model selection

### 2. Web Interface (`mcp_web_interface/`)
**Django-based web application providing a modern chat interface**

- **Chat Interface**: Real-time conversation with AI models
- **Custom Prompts**: Template management for reusable queries
- **Model Management**: Easy switching between different AI models
- **History Persistence**: Complete chat history storage
- **Response Tracking**: Performance monitoring for model execution times

**Key Features:**
- Modern, responsive UI with Bootstrap styling
- Full-screen chat experience
- Copy and download functionality for responses (in progress)
- Persistent chat history with SQLite/PostgreSQL support
- Real-time streaming responses (in progress)

## 🔧 Technical Stack

### Backend Technologies
- **FastAPI**: High-performance API framework for MCP server
- **Django**: Web framework for the interface layer
- **Pandas**: Data manipulation and analysis
- **SQLite/PostgreSQL**: Database storage
- **Uvicorn**: ASGI server for FastAPI

### AI & Data Integration
- **Google Generative AI**: Gemini model integration
- **OpenAI API**: GPT model support
- **Cerebras Cloud**: Qwen model integration
- **Open-Meteo API**: Weather data source
- **Requests Cache**: API response caching

### Frontend Technologies
- **HTML/CSS/JavaScript**: Core web technologies
- **Bootstrap**: For Icons

## 📊 Data Flow

```
User Query → Web Interface → MCP Server → AI Model → Function Call → AI Model → Filter Query → Weather API → Data Processing → Response
```

1. **User Input**: Natural language weather query
2. **Model Processing**: AI model interprets the query determines which tool to call (if any) 
3. **Function Calling**: Model calls appropriate weather functions
4. **Model Processing**: AI Model interprets the query and generates formulas to perform on weather data
5. **Data Retrieval**: Weather data fetched from Open-Meteo API
6. **Data Processing**: Pandas-based filtering and transformation
7. **Response Generation**: Processed data returned to user

## 🎯 Key Capabilities

### Weather Data Features
- **Hourly Forecasts**: Up to 16 days of detailed weather data
- **Multiple Parameters**: Temperature, humidity, precipitation, wind speed, cloud cover
- **Geocoding**: Automatic location resolution from city/state names
- **Time Zone Support**: America/New_York timezone handling
- **Unit Conversion**: Fahrenheit temperatures, MPH wind speeds

### AI-Powered Analysis
- **Natural Language Queries**: "What's the weather in Miami, FL tomorrow?"
- **Advanced Filtering**: "Show temperatures above 80°F"
- **Data Transformation**: "Create a column for heat index"
- **Trend Analysis**: "Summarize weather patterns for the week"

### Data Processing Capabilities
- **Dynamic Filtering**: SQL-like queries on weather data
- **Column Creation**: Formula-based new column generation
- **Data Aggregation**: Statistical analysis and summaries
- **Export Options**: Download results in various formats

## 🔌 API Endpoints

### MCP Server Endpoints
- `POST /weather/data`: Standard weather data retrieval
- `POST /weather/data/stream`: Streaming weather data with real-time updates

### Web Interface Endpoints
- `/`: Main chat interface
- `/custom_prompts/`: Prompt template management
- `/chat/`: Chat API endpoints

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.9+
- API keys for AI models (Gemini, OpenAI, Cerebras)
- Virtual environment (recommended)

### Quick Start
1. **Clone and setup MCP server**:
   ```bash
   cd mcp_server
   source env_keys.sh  # Add your API keys
   uvicorn router:app --reload --port 8080
   ```

2. **Setup web interface**:
   ```bash
   cd mcp_web_interface
   python manage.py migrate
   python manage.py runserver
   ```

3. **Access the application**:
   - Web interface: `http://localhost:8000`
   - MCP server: `http://localhost:8080`

## 📈 Performance Features

- **Caching**: 1-hour cache for weather API responses
- **Retry Logic**: Automatic retry on API failures
- **Streaming**: Real-time response updates
- **Execution Tracking**: Model and function performance monitoring
- **Error Handling**: Graceful error recovery and user feedback

## 🔮 Future Enhancements

- **Extended Forecast**: Support for longer-term weather predictions
- **Additional Weather Sources**: Integration with multiple weather APIs
- **Mobile Interface**: Responsive design for mobile devices
- **API Rate Limiting**: Enhanced request management
- **Complex Data Manipluation**: Data summaries, trends, graphs, etc. 

## 📝 License

This project is licensed under the MIT License.

---

*This application demonstrates the power of combining AI models with real-time data APIs to create intelligent, user-friendly weather analysis tools.*

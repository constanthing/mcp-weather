# MCP Server - AI Chat Application

A Django-based web application that provides an interface for interacting with multiple AI models through a Model Context Protocol (MCP) server. The application supports chat functionality, custom prompts, and integration with various AI models including Gemini, OpenAI, and Cerebras.

## 🚀 Features

### Core Functionality
- **Multi-Model Chat Interface**: Support for multiple AI models including:
  - Gemini 2.5 Flash
  - Gemini 2.5 Pro
  - Cerebras (Qwen 3-32B)
  - OpenAI GPT-4.1 Mini

- **Real-time Chat**: Stream responses from AI models with live updates
- **Chat History**: Persistent storage of chat conversations with full history
- **Custom Prompts**: Create, edit, and manage reusable prompt templates
- **Weather Data Integration**: Specialized weather data retrieval and analysis capabilities

### User Interface
- **Modern Web Interface**: Clean, responsive design with Bootstrap icons
- **Model Selection**: Easy switching between different AI models
- **Expandable Chat**: Full-screen chat experience
- **Copy & Download**: Copy responses and download function results
- **Response Time Tracking**: Monitor model and function execution times

## 🏗️ Architecture

### Technology Stack
- **Backend**: Django 5.2.3 (Python web framework)
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Frontend**: HTML, CSS, JavaScript with Bootstrap styling
- **AI Integration**: HTTP API communication with MCP server
- **Data Processing**: Pandas for data manipulation and HTML table generation

### Project Structure
```
mcp_server/
├── mcp/                          # Django project settings
│   ├── settings.py               # Django configuration
│   ├── urls.py                   # URL routing
│   └── wsgi.py                   # WSGI application
├── mcp_server/                   # Main Django app
│   ├── models.py                 # Database models
│   ├── views.py                  # View logic and API endpoints
│   ├── mcp_server_api.py        # MCP server integration
│   ├── templates/                # HTML templates
│   │   ├── chat.html            # Chat interface
│   │   ├── custom_prompts.html  # Custom prompts management
│   │   └── base.html            # Base template
│   └── static/                   # Static assets
│       ├── css/                  # Stylesheets
│       ├── js/                   # JavaScript files
│       └── icons/                # Application icons
├── requirements.txt              # Python dependencies
└── manage.py                     # Django management script
```

### Database Models

#### Chat Model
- **UUID Primary Key**: Unique identifier for each chat
- **Title**: Optional chat title (max 30 characters)
- **History**: JSON storage of chat messages
- **History Full**: Complete conversation history
- **Model**: Selected AI model identifier
- **Created At**: Timestamp of chat creation

#### CustomPrompt Model
- **UUID Primary Key**: Unique identifier
- **Name**: Prompt name (max 255 characters)
- **Prompt**: The actual prompt text
- **Created At**: Timestamp of creation

#### DeletedChat Model
- **Archive Storage**: Stores deleted chat data for potential recovery

#### FunctionResponse Model
- **Response Storage**: Stores function execution results

## 🔧 Installation & Setup

### Prerequisites
- Python 3.9+
- Virtual environment (recommended)
- MCP Server running on localhost:8080

### Installation Steps

`
pip install Django pandas tabulate requests 
`

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mcp_server
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

5. **Start the development server**
   ```bash
   source setup.sh
   python manage.py runserver
   ```

6. **Access the application**
   - Open your browser and navigate to `http://localhost:8000`
   - The application will be available at the root URL

## 📖 Usage

### Starting a New Chat
1. Navigate to the chat interface
2. Select your preferred AI model from the dropdown
3. Type your message in the input field
4. Press Enter or click the send button
5. View the AI response in real-time

### Managing Custom Prompts
1. Access the custom prompts page
2. Create new prompts with descriptive names
3. Edit existing prompts as needed
4. Use prompts in chat by clicking on them

### Chat Features
- **Model Switching**: Change AI models (creates new chat)
- **History Persistence**: All conversations are automatically saved
- **Response Time Tracking**: Monitor how long models take to respond
- **Function Results**: Download or copy function execution results

## 🔌 API Integration

### MCP Server Communication
The application communicates with an external MCP server running on `localhost:8080`:

- **Weather Data Endpoint**: `/weather/data`
- **Streaming Endpoint**: `/weather/data/stream`

### Supported Models
- `gemini-2.5-flash`: Google's Gemini 2.5 Flash model
- `gemini-2.5-pro`: Google's Gemini 2.5 Pro model
- `qwen-3-32b`: Cerebras Qwen 3-32B model
- `gpt-4.1-mini`: OpenAI's GPT-4.1 Mini model

## 🛠️ Development

### Key Dependencies
- **Django 5.2.3**: Web framework
- **Pandas 2.3.0**: Data manipulation
- **Requests 2.32.4**: HTTP client
- **Google Generative AI**: Gemini model integration

### Environment Configuration
- **DEBUG**: Set to `True` for development
- **ALLOWED_HOSTS**: Configured for localhost and production domain
- **Database**: SQLite for development

### Customization
- **Models**: Add new AI models in `views.py`
- **Templates**: Modify HTML templates in `templates/`
- **Styling**: Update CSS files in `static/css/`
- **JavaScript**: Modify behavior in `static/js/`

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For questions or issues, please open an issue in the repository or contact the development team.

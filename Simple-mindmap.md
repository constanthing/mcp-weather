# MCP Weather App - Folder Structure

## Main Folders

### mcp_server/
- **What it does**: Backend server that handles AI and weather data
- **Contains**: 
  - API endpoints for weather requests
  - AI model connections (Gemini, OpenAI, Cerebras)
  - Weather data processing
  - Function calling logic

### mcp_web_interface/
- **What it does**: Web application that users interact with
- **Contains**:
  - Chat interface for users
  - Database for storing conversations
  - Templates for web pages
  - Static files (CSS, JavaScript, images)

## Subfolders

### mcp_server/models/
- **What it does**: Contains AI model connection files
- **Contains**: gemini.py, cerebras.py, openai.py

### mcp_web_interface/mcp_server/
- **What it does**: Main Django app folder
- **Contains**: Database models, views, templates, static files

### mcp_web_interface/mcp/
- **What it does**: Django project settings
- **Contains**: settings.py, urls.py, wsgi.py

### mcp_web_interface/mcp_server/templates/
- **What it does**: HTML pages for the web interface
- **Contains**: chat.html, custom_prompts.html, base.html

### mcp_web_interface/mcp_server/static/
- **What it does**: Frontend files (styling, scripts, images)
- **Contains**: CSS, JavaScript, icons

### mcp_web_interface/mcp_server/migrations/
- **What it does**: Database change history
- **Contains**: Database schema updates

from django.core.management.base import BaseCommand
from mcp_server.test_cerebras_agent import get_response

class Command(BaseCommand):
    help = 'Test the Cerebras agent with tools'

    def handle(self, *args, **options):
        self.stdout.write("Testing Cerebras Agent with Tools...")
        
        # Initialize empty message history
        messages = []
        
        # Test message that should trigger weather tool
        test_message = "What's the weather like in San Francisco, California today?"
        
        self.stdout.write(f"Message: {test_message}")
        self.stdout.write("-" * 50)
        
        try:
            # Get response from the agent
            for response_chunk in get_response(messages, test_message, "llama3.1-8b"):
                if isinstance(response_chunk, str):
                    # Handle streaming responses
                    if "[DELIMITER]" in response_chunk:
                        parts = response_chunk.split("[DELIMITER]")
                        for part in parts:
                            if part.strip():
                                try:
                                    data = eval(part)
                                    if isinstance(data, dict):
                                        if 'text' in data:
                                            self.stdout.write(f"Status: {data.get('text', '')}")
                                        elif 'status' in data and data['status'] == 'tool':
                                            self.stdout.write(f"Tool Data: {data.get('data', {})}")
                                        elif 'status' in data and data['status'] == 'response':
                                            self.stdout.write(f"Final Response: {data.get('text', '')}")
                                            self.stdout.write(f"Response Time: {data.get('model_response_time', 0)}s")
                                            return
                                except:
                                    self.stdout.write(f"Raw: {part}")
                    else:
                        self.stdout.write(f"Raw response: {response_chunk}")
                elif isinstance(response_chunk, dict):
                    # Handle final response
                    if response_chunk.get('status') == 'response':
                        self.stdout.write(f"Final Response: {response_chunk.get('text', '')}")
                        self.stdout.write(f"Response Time: {response_chunk.get('model_response_time', 0)}s")
                        return
                    elif response_chunk.get('status') == 'error':
                        self.stdout.write(f"Error: {response_chunk.get('error', '')}")
                        return
                        
        except Exception as e:
            self.stdout.write(f"Error testing Cerebras agent: {e}")
            return None 
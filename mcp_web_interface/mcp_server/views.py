import json
import time
import traceback

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Chat, CustomPrompt
from django.views.decorators.http import require_http_methods 
from django.http import StreamingHttpResponse

from .mcp_server_api import get_mcp_server_response, get_mcp_server_response_stream

models = [
    {
        "name": "Gemini 2.5-Flash",
        "identifier": "gemini-2.5-flash"
    },
    {
        "name": "Gemini 2.5-Pro",
        "identifier": "gemini-2.5-pro"
    },
    {
        "name": "Cerebras (qwen)",
        "identifier": "qwen-3-32b"
    },
    {
        "name": "OpenAI (gpt-4.1-mini)",
        "identifier": "gpt-4.1-mini"
    },
]

# Create your views here.
def index(request):
    chats = Chat.objects.all().order_by('-created_at')
    custom_prompts = CustomPrompt.objects.all()

    context = {
        'chats': chats,
        'custom_prompts': custom_prompts
    }

    return render(request, 'custom_prompts.html', context)

"""
CHATS
"""
def chat(request, chat_id=None):
    if request.method == "GET":
        return get_chat(request, chat_id)
    elif request.method == "POST":
        if not chat_id:
            return create_chat(request)
        else:
            # update chat
            return update_chat(request, chat_id)
    elif request.method == "DELETE":
        return delete_chat(request, chat_id)
        

def create_chat(request):
    chat = Chat.objects.create()

    data = json.loads(request.body.decode('utf-8'))
    model_identifier = data.get('model_name')

    if not model_identifier:
        return JsonResponse({'success': False, 'error': 'model_name is required'}, status=400)

    if "grok" in model_identifier or "qwen" in model_identifier or "llama" in model_identifier:
        messages = [
            {
                "role": "system",
                "content": """
        You are a weather assistant. Do not guess, infer, or imagine any weather-related data or information. You must only use the tools and functions explicitly defined by the user to retrieve and present information. If a user asks a question that cannot be answered directly by one of the available tools, clearly state that you cannot provide an answer.

        - Do NOT fabricate weather conditions, forecasts, historical data, or location-based information.
        - Do NOT use prior knowledge, assumptions, or context outside the current tool-defined capabilities/chat history.
        - ONLY use the available tools and return data as provided.

        Your responses must remain factual, concise, and grounded only in tool-based outputs.

        Do not interpret the data. Analyze user prompt and determine what what to do with data.
        Do not filter the data. Always use tools to do anything with data.

        Convert data to markdown table.
            """
            },
        ]
        chat.history = json.dumps(messages) 
    
    chat.model = model_identifier

    chat.save()

    return JsonResponse({'success': True, 'chat_id': chat.id})


def get_chat(request, chat_id):
    """
    Chat can be accessed two ways:
    - from existing chat (chat row created in db)
    - from new chat (chat row not yet created in db)

    New chat we don't create a row in db until user sends a message. 
    """

    chats = Chat.objects.all().order_by('-created_at')
    custom_prompts = CustomPrompt.objects.all().order_by('-created_at')
    
    context = {
        'chats': chats,
        'custom_prompts': custom_prompts,
    }

    if not chat_id:
        # default model is always gemini-2.5-flash
        model_name = request.GET.get("model")
        if not model_name:
            model_name = "gemini-2.5-flash"

        selected_model = None
        available_models = []
        for model in models:
            if model['identifier'] == model_name:
                selected_model = model
            else:
                available_models.append(model)

        context['model'] = selected_model 
        context['available_models'] = available_models 

        return render(request, "chat.html", context)

    chat = Chat.objects.get(id=chat_id)

    # model and available models
    selected_model = None
    available_models = []
    for model in models:
        if model['identifier'] == chat.model:
            selected_model = model
        else:
            available_models.append(model)

    context['model'] = selected_model 
    context['available_models'] = available_models 

    history = json.loads(chat.history)

    print("===HISTORY===")
    print(json.dumps(history, indent=4))
    print("===HISTORY===")

    chat_history_pairs = []
    index = 0
    pair = []
    for chat in history:
        # skip system instructions (usually only for grok)
        if chat["role"] == "system" or chat["role"] == "tool":
            print("skipped")
            continue

        try:
            text = ""
            if "parts" in chat:
                for item in chat["parts"]:
                    text += item["text"]
            else:
                text = chat["content"]

            try:
                model_response_time = chat["model_response_time"]
            except:
                model_response_time = None

            pair.append({"role": chat["role"], "text": text, "model_response_time": model_response_time})
            index += 1
        except:
            continue
        if index == 2:
            chat_history_pairs.append(pair)
            pair = []
            index = 0

    context['chat_history'] = chat_history_pairs
    context['chat_id'] = chat_id

    return render(request, 'chat.html', context)

def update_chat(request, chat_id):

    data = json.loads(request.body.decode('utf-8'))
    message = data.get('message')

    def stream_response():
        try:
            yield json.dumps({
                "text": "Getting chat " + str(chat_id)
            }) + "[DELIMITER]"
            chat = Chat.objects.get(id=chat_id)


            if not chat:
                yield json.dumps({
                    "status": "error",
                    "error": "Chat not found"
                }) + "[DELIMITER]"
                return

            if message == "":
                yield json.dumps({
                    "status": "error",
                    "error": "Message is empty"
                }) + "[DELIMITER]"
                return

            print("loading chat history")


            yield json.dumps({
                "text": "Loading chat history"
            }) + "[DELIMITER]"
            # Parse existing history from string
            history = json.loads(chat.history) if chat.history else []
            history.append({
                "role": "user",
                "content": message.strip()
            })
            chat.title = message[:29]

            print("initiating agent response")

            yield json.dumps({
                "text": "Waiting on MCP server response..."
            }) + "[DELIMITER]"

            response_data = None

            # get response from mcp server
            for response in get_mcp_server_response(message, chat.model):
                # if string, yield response to client
                if type(response) != str and (response.get("status") == "response" or response.get("status") == "error"):
                    response_data = response
                    break
                yield response

            print(response_data)
            if response_data.get("status") == "error":
                yield json.dumps({
                    "status": "error",
                    "error": response_data.get("error")
                }) + "[DELIMITER]"
                return

            response = response_data["text"]

            model_response_time = response_data["model_response_time"]
            function_response_time = response_data["function_response_time"]
            function_name = response_data["function_name"]
            function_args = response_data["function_args"]

            yield json.dumps({
                "text": "Saving user prompt and agent response to chat history"
            }) + "[DELIMITER]"

            history.append({
                "role": "assistant",
                "content": response,
                "model_response_time": model_response_time,
                "function_response_time": function_response_time,
                "function_name": function_name,
                "function_args": function_args,
            })

            # Save as JSON string
            chat.history = json.dumps(history)
            chat.save()

            yield json.dumps({
                "text": "Done! Sending response to client..."
            }) + "[DELIMITER]"

            data = {
                "reply": response,
                "model_response_time": model_response_time,
                "function_response_time": function_response_time,
                "function_name": function_name,
                "function_args": function_args,
                "chat_id": str(chat_id),
            }

            yield json.dumps({
                "status": "done",
                "data": data
            }) + "[DELIMITER]"
        except BrokenPipeError:
            print("❌ Stream Aborted By User")
        except Exception as e:
            print(e)
            yield json.dumps({
                "status": "error",
                "error": "<p>❌ <b>Server error:</b> " + str(traceback.format_exc()) + "</p>"
            }) + "[DELIMITER]"
        finally:
            print("👍 Stream Closed")

    return StreamingHttpResponse(stream_response(), content_type='text/event-stream')
    # return JsonResponse({'success': True, 'data': data})

def delete_chat(request, chat_id):
    try: 
        chat = Chat.objects.get(id=chat_id)
        chat.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

"""
CUSTOM PROMPTS
"""

def custom_prompt_actions(request, custom_prompt_id):
    if request.method == 'DELETE':
        return delete_custom_prompt(request, custom_prompt_id)
    elif request.method == 'PUT':
        return edit_custom_prompt(request, custom_prompt_id)
    elif request.method == 'GET':
        return get_custom_prompt(request, custom_prompt_id)


def create_custom_prompt(request):
    data = json.loads(request.body.decode('utf-8'))
    name = data.get('name')
    prompt = data.get('prompt')

    custom_prompt = CustomPrompt.objects.create(name=name, prompt=prompt)

    data = {
        'id': custom_prompt.id, 
        'name': custom_prompt.name,
        'prompt': custom_prompt.prompt
    }

    return JsonResponse({'success': True, 'prompt': data})


@require_http_methods(["DELETE"])
def delete_custom_prompt(request, custom_prompt_id):
    if not custom_prompt_id:
        return JsonResponse({'success': False, 'error': 'custom_prompt_id is required'}, status=400)

    custom_prompt = CustomPrompt.objects.get(id=custom_prompt_id)

    if not custom_prompt:
        return JsonResponse({'success': False, 'error': 'custom_prompt not found'}, status=404)

    custom_prompt.delete()

    return JsonResponse({'success': True})


@require_http_methods(["GET"])
def get_custom_prompt(request, custom_prompt_id):
    if not custom_prompt_id:
        return JsonResponse({'success': False, 'error': 'custom_prompt_id is required'}, status=400)

    custom_prompt = CustomPrompt.objects.get(id=custom_prompt_id)

    if not custom_prompt:
        return JsonResponse({'success': False, 'error': 'custom_prompt not found'}, status=404)

    data = {
        'name': custom_prompt.name,
        'prompt': custom_prompt.prompt
    }

    return JsonResponse({'success': True, 'prompt': data})


@require_http_methods(["PUT"])
def edit_custom_prompt(request, custom_prompt_id):
    if not custom_prompt_id:
        return JsonResponse({'success': False, 'error': 'custom_prompt_id is required'}, status=400)

    data = json.loads(request.body.decode('utf-8'))
    name = data.get('name')
    prompt = data.get('prompt')

    custom_prompt = CustomPrompt.objects.get(id=custom_prompt_id)

    custom_prompt.name = name
    custom_prompt.prompt = prompt
    custom_prompt.save()

    data = {
        'id': custom_prompt.id,
        'name': custom_prompt.name,
        'prompt': custom_prompt.prompt
    }

    return JsonResponse({'success': True, 'prompt': data})

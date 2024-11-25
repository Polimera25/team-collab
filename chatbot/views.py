from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import ollama  # Ensure this is the correct Python package for Ollama integration

# Initialize the Ollama client
ollama_client = ollama.Client()

@csrf_exempt
def chatbot_response(request):
    if request.method == 'POST':
        try:
            # Parse the JSON body
            body = json.loads(request.body)
            user_input = body.get('input')  # Expecting JSON with an 'input' key

            if not user_input:
                return JsonResponse({'error': 'No input provided'}, status=400)

            # Define the model you want to use
            model_name = 'qwen2.5:1.5b'  # Specify the correct model name

            # Use the chat method and pass the model_name
            response = ollama_client.chat(model=model_name, messages=[{'role': 'user', 'content': user_input}])

            # Extract the content from the response message
            prediction = response.get('message', {}).get('content', 'No response generated')

            return JsonResponse({'prediction': prediction})

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'POST request required'}, status=405)
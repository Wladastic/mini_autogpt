import os
import requests
from utils.log import log, save_debug
import think.memory as memory
from dotenv import load_dotenv

def handle_model_not_found_error(response, server_type):
    """Handle model not found errors with user-friendly messages"""
    try:
        error_data = response.json()
        if server_type == "lmstudio":
            log("No models loaded in LM Studio.")
            log("Please load a model in the LM Studio developer page.")
        elif server_type == "ollama":
            model = os.getenv("OLLAMA_MODEL")
            log(f"Model {model} not found in Ollama.")
            log(f"Please run: ollama pull {model}")
        elif server_type == "oobabooga":
            log("Model not found in Oobabooga.")
            log("Please ensure you have loaded a model.")
        
        if os.getenv('DEBUG', 'false').lower() == 'true':
            log(f"Detailed error: {error_data}")
    except Exception as e:
        log(f"Error parsing response: {e}")
    return response

def test_connection():
    """Test connection to LLM server based on server type."""
    api_url = os.getenv("API_URL")
    llm_server_type = os.getenv("LLM_SERVER_TYPE")

    try:
        log(f"Testing {llm_server_type} connection...")
        headers = {"Content-Type": "application/json"}

        if llm_server_type == "lmstudio":
            # LM Studio uses OpenAI-style API, test models endpoint
            base_url = api_url.rsplit('/', 1)[0]  # Remove 'chat/completions'
            test_url = f"{base_url}/models"
            response = requests.get(test_url, timeout=5)
            save_debug({"url": test_url}, response)
            
            if response.status_code == 404:
                return "No models loaded in LM Studio. Please load a model first."
            elif response.status_code != 200:
                return f"LM Studio server error: {response.status_code}"

        elif llm_server_type == "ollama":
            # Test Ollama with a simple ping
            response = requests.get(api_url.rsplit('/', 1)[0] + "/version", timeout=5)
            if response.status_code != 200:
                return "Ollama server is not responding correctly."
            
            # Check if the specified model is available
            model = os.getenv("OLLAMA_MODEL")
            if model:
                model_url = f"{api_url.rsplit('/', 1)[0]}/tags"
                response = requests.get(model_url, timeout=5)
                save_debug({"url": model_url}, response)
                if not any(model in str(tag) for tag in response.json().get("models", [])):
                    return f"Model {model} not found in Ollama. Please run: ollama pull {model}"

        elif llm_server_type == "oobabooga":
            # Oobabooga doesn't have a specific health check endpoint
            # Just verify the server is responding
            response = requests.get(api_url, timeout=5)
            save_debug({"url": api_url}, response)
            if response.status_code != 200:
                return "Oobabooga server is not responding correctly."

        return None  # No error

    except requests.exceptions.RequestException as e:
        return f"Could not connect to {llm_server_type} server at {api_url}. Is it running?"

def one_shot_request(prompt, system_context):
    history = []
    history.append({"role": "system", "content": system_context})
    history.append({"role": "user", "content": prompt})
    response = llm_request(history)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        log("Error in one_shot_request")
        return None

def llm_request(history):
    load_dotenv()
    temperature = os.getenv("TEMPERATURE")
    max_tokens = os.getenv("MAX_TOKENS")
    truncation_length = os.getenv("TRUNCATION_LENGTH")
    max_new_tokens = os.getenv("MAX_NEW_TOKENS")

    data = {
        "mode": "instruct",
        "messages": history,
        "temperature": temperature,
        "user_bio": "",
        "max_tokens": max_tokens,
        "truncation_length": truncation_length,
        "max_new_tokens": max_new_tokens,
    }
    return send(data=data)

def send(data):
    # load environment variables
    load_dotenv()
    api_url = os.getenv("API_URL")
    llm_server_type = os.getenv("LLM_SERVER_TYPE", "default")  # Default to "default" if not set

    headers = {"Content-Type": "application/json"}

    try:
        log(f"Sending request to API URL: {api_url} with LLM server type: {llm_server_type}")
        if llm_server_type == "lmstudio":
            # Get LMStudio model from environment
            lmstudio_model = os.getenv("LMSTUDIO_MODEL")
            payload = {
                "messages": data["messages"],
                "temperature": float(data["temperature"]),
                "max_tokens": int(data["max_tokens"]),
                "model": lmstudio_model,
            }
            log(f"Payload: {payload}")
            response = requests.post(api_url, headers=headers, json=payload)
            save_debug(payload, response)
            if response.status_code == 404:
                return handle_model_not_found_error(response, "lmstudio")
        elif llm_server_type == "ollama":
            # Assuming ollama uses its own specific format
            ollama_model = os.getenv("OLLAMA_MODEL", "default")  # Default to "default" if not set
            payload = {
                "prompt": data["messages"][-1]["content"],
                "model": ollama_model,
                "stream": False,
            }
            log(f"Payload: {payload}")
            response = requests.post(api_url, headers=headers, json=payload)
            save_debug(payload, response)
            if response.status_code == 404:
                return handle_model_not_found_error(response, "ollama")
            elif response.status_code != 200:
                log(f"Error from Ollama API: {response.status_code} - {response.text}")
                return None
        elif llm_server_type == "oobabooga":
            # Assuming oobabooga uses the OpenAI API format
            payload = {
                "messages": data["messages"],
                "temperature": float(data["temperature"]),
                "max_tokens": int(data["max_tokens"]),
            }
            log(f"Payload: {payload}")
            response = requests.post(api_url, headers=headers, json=payload)
            save_debug(payload, response)
            if response.status_code == 404:
                return handle_model_not_found_error(response, "oobabooga")
        else:
            log(f"Payload: {data}")
            response = requests.post(api_url, headers=headers, json=data)
            save_debug(data, response)
        return response
    except Exception as e:
        log("Exception when talking to API:")
        log(e)
        exit(1)

def build_context(history, conversation_history, message_history):
    context = ""
    if conversation_history:
        context += "Context:\n"
        for convo in conversation_history:
            if convo:
                context += str(convo)
    if message_history:
        context += "\nMessages:\n"
        for message in message_history:
            if message:
                context += str(message)
    memories = memory.load_memories()
    if memories:
        context += "\nMemories:\n"
        for mem in memories:
            context += mem
    if context:
        history.append(
            {
                "role": "user",
                "content": str(context),
            }
        )
    return history

def build_prompt(base_prompt):
    prompt = []
    prompt.append({"role": "system", "content": base_prompt})

    return prompt

import os
import time
import traceback
import requests
from think.think import debug_log
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

        if os.getenv("DEBUG", "false").lower() == "true":
            log(f"Detailed error: {error_data}")
    except Exception as e:
        log(f"Error parsing response: {e}")
    return response

def get_base_url(api_url, server_type):
    """Get the base URL for different server types."""
    if server_type == "lmstudio":
        # Clean up URL removing any whitespace and trailing slashes
        base = api_url.strip()
        
        # Extract base path up to /v1
        if "/v1/chat/completions" in base:
            base = base.split("/v1/")[0] + "/v1"
        elif "/v1/" in base:
            base = base.split("/v1/")[0] + "/v1"
        elif not base.endswith("/v1"):
            if base.endswith("/"):
                base = base.rstrip("/") + "/v1"
            else:
                base = base + "/v1"
        
        return base.rstrip("/")  # Ensure no trailing slash
    else:
        # For other servers, just remove the last part
        return api_url.rsplit("/", 1)[0].strip()

def test_connection():
    """Test connection to LLM server based on server type."""
    api_url = os.getenv("API_URL", "").strip()  # Strip whitespace from API URL
    llm_server_type = os.getenv("LLM_SERVER_TYPE")

    if not api_url:
        return "API URL is not configured"

    try:
        log(f"Testing {llm_server_type} connection at {api_url}")

        if llm_server_type == "lmstudio":
            base_url = get_base_url(api_url, llm_server_type)  # No stripping here
            test_url = f"{base_url}/models"  # This will now be /v1/models as required
            log(f"Testing LM Studio models endpoint: {test_url}")
            response = requests.get(test_url, timeout=5)
            save_debug({"url": test_url}, response)

            if response.status_code == 404:
                return "No models loaded in LM Studio. Please load a model first."
            elif response.status_code != 200:
                return f"LM Studio server error: {response.status_code}"

        elif llm_server_type == "ollama":
            base_url = get_base_url(api_url, llm_server_type)
            log(f"Testing Ollama version endpoint: {base_url}/version")
            response = requests.get(base_url + "/version", timeout=5)
            if response.status_code != 200:
                return "Ollama server is not responding correctly."

            model = os.getenv("OLLAMA_MODEL")
            if model:
                model_url = f"{base_url}/tags"
                log(f"Testing Ollama model availability: {model_url}")
                response = requests.get(model_url, timeout=5)
                save_debug({"url": model_url}, response)
                if not any(model in str(tag) for tag in response.json().get("models", [])):
                    return f"Model {model} not found in Ollama."

        elif llm_server_type == "oobabooga":
            log(f"Testing Oobabooga endpoint: {api_url}")
            response = requests.get(api_url, timeout=5)
            save_debug({"url": api_url}, response)
            if response.status_code != 200:
                return "Oobabooga server is not responding correctly."

        log("Connection test successful")
        return None  # No error

    except requests.exceptions.RequestException as e:
        error_msg = f"Could not connect to {llm_server_type} server at {api_url}"
        log(f"{error_msg}: {str(e)}")
        return error_msg

def llm_request(history):
    """Process a request to the LLM with the given conversation history."""
    try:
        load_dotenv()
        data = {"messages": history}
        response = send(data=data)

        # If response is None, error was already logged
        if response is None:
            return None

        try:
            response_data = response.json()
        except Exception as e:
            log(f"Error parsing JSON response: {str(e)}")
            return None

        # Check for missing choices
        if "choices" not in response_data:
            log("Invalid response - missing choices")
            debug_log(f"Full response: {response_data}")
            return None

        return response

    except Exception as e:
        log(f"Error in llm_request: {str(e)}")
        debug_log(traceback.format_exc())
        return None

def send(data, max_retries=3, retry_delay=5):
    """Send the actual request to the LLM server.
    
    Args:
        data: The data to send to the LLM
        max_retries: Maximum number of retries on failure (default: 3)
        retry_delay: Seconds to wait between retries (default: 5)
    """
    load_dotenv()
    api_url = os.getenv("API_URL", "").strip()  # Strip whitespace from API URL
    llm_server_type = os.getenv("LLM_SERVER_TYPE", "lmstudio")
    headers = {"Content-Type": "application/json"}

    if not api_url:
        log("API URL is not configured")
        log("Fatal error - exiting")
        exit(1)

    retry_count = 0
    while retry_count < max_retries:
        try:
            if retry_count > 0:
                log(f"Retrying... (Attempt {retry_count + 1}/{max_retries})")
            else:
                log("Thinking...")

            if llm_server_type == "lmstudio":
                lmstudio_model = os.getenv("LMSTUDIO_MODEL")
                temperature = float(os.getenv("TEMPERATURE", "0.8"))
                max_tokens = int(os.getenv("MAX_TOKENS", "4000"))
                
                # Construct the chat completions endpoint
                base_url = get_base_url(api_url, "lmstudio")  # Let get_base_url handle slashes
                chat_url = f"{base_url}/chat/completions"  # This will now be /v1/chat/completions as required
                log(f"Sending request to LM Studio: {chat_url}")
                
                payload = {
                    "messages": data["messages"],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "model": lmstudio_model,
                }
                response = requests.post(chat_url, headers=headers, json=payload, timeout=30)
                save_debug({"url": chat_url, "payload": payload}, response)
                
                try:
                    response_data = response.json()
                    if "error" in response_data:
                        log(f"Error from LMStudio: {response_data['error']}")
                        # Model errors are fatal
                        log("Fatal error - exiting")
                        exit(1)
                except Exception as e:
                    log(f"Error parsing LMStudio response: {e}")
                    # JSON parse errors are fatal
                    log("Fatal error - exiting")
                    exit(1)

                return response

            elif llm_server_type == "ollama":
                ollama_model = os.getenv("OLLAMA_MODEL", "default")
                # Construct the generate endpoint
                base_url = get_base_url(api_url, "ollama")
                generate_url = f"{base_url}/generate"
                log(f"Sending request to Ollama: {generate_url}")
                
                payload = {
                    "prompt": data["messages"][-1]["content"],
                    "model": ollama_model,
                    "stream": False,
                }
                response = requests.post(generate_url, headers=headers, json=payload, timeout=30)
                save_debug(payload, response)

                if response.status_code != 200:
                    log(f"Error from Ollama: {response.status_code}")
                    if response.status_code == 404:
                        log(f"Model {ollama_model} not found. Try: ollama pull {ollama_model}")
                        # Model not found is a fatal error
                        log("Fatal error - exiting")
                        exit(1)
                    # Other status codes might be temporary
                    retry_count += 1
                    continue

                return response

            elif llm_server_type == "oobabooga":
                temperature = float(os.getenv("TEMPERATURE", "0.7"))
                max_tokens = int(os.getenv("MAX_TOKENS", "2000"))
                payload = {
                    "messages": data["messages"],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
                response = requests.post(api_url, headers=headers, json=payload, timeout=30)
                save_debug(payload, response)

                if response.status_code != 200:
                    log(f"Error from Oobabooga: {response.status_code}")
                    # Non-200 responses from Oobabooga are fatal
                    log("Fatal error - exiting")
                    exit(1)

                return response

            else:
                log(f"Unknown LLM server type: {llm_server_type}")
                # Invalid configuration is fatal
                log("Fatal error - exiting")
                exit(1)

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            retry_count += 1
            if retry_count < max_retries:
                log(f"Connection error: {str(e)}")
                log(f"Waiting {retry_delay} seconds before retrying...")
                time.sleep(retry_delay)
                continue
            log(f"Failed to connect after {max_retries} attempts. Error: {str(e)}")
            log("Fatal error - exiting")
            exit(1)

        except Exception as e:
            log(f"Unexpected error: {str(e)}")
            debug_log(traceback.format_exc())
            log("Fatal error - exiting")
            exit(1)

def one_shot_request(prompt, system_context):
    """Send a single request with system context and user prompt."""
    history = []
    history.append({"role": "system", "content": system_context})
    history.append({"role": "user", "content": prompt})
    response = llm_request(history)

    if response is None:
        return None

    try:
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        log(f"Error extracting content: {str(e)}")
        return None

def build_context(history, conversation_history, message_history):
    """Build context from conversation history and messages."""
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
    """Build initial prompt with system message."""
    return [{"role": "system", "content": base_prompt}]

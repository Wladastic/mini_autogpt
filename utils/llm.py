import os
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


def test_connection():
    """Test connection to LLM server based on server type."""
    api_url = os.getenv("API_URL")
    llm_server_type = os.getenv("LLM_SERVER_TYPE")

    try:
        log(f"Testing {llm_server_type} connection...")

        if llm_server_type == "lmstudio":
            base_url = api_url.rsplit("/", 1)[0]
            test_url = f"{base_url}/models"
            response = requests.get(test_url, timeout=5)
            save_debug({"url": test_url}, response)

            if response.status_code == 404:
                return "No models loaded in LM Studio. Please load a model first."
            elif response.status_code != 200:
                return f"LM Studio server error: {response.status_code}"

        elif llm_server_type == "ollama":
            response = requests.get(api_url.rsplit("/", 1)[0] + "/version", timeout=5)
            if response.status_code != 200:
                return "Ollama server is not responding correctly."

            model = os.getenv("OLLAMA_MODEL")
            if model:
                model_url = f"{api_url.rsplit('/', 1)[0]}/tags"
                response = requests.get(model_url, timeout=5)
                save_debug({"url": model_url}, response)
                if not any(
                    model in str(tag) for tag in response.json().get("models", [])
                ):
                    return f"Model {model} not found in Ollama."

        elif llm_server_type == "oobabooga":
            response = requests.get(api_url, timeout=5)
            save_debug({"url": api_url}, response)
            if response.status_code != 200:
                return "Oobabooga server is not responding correctly."

        return None

    except requests.exceptions.RequestException as e:
        return f"Could not connect to {llm_server_type} server at {api_url}."


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


def send(data):
    """Send the actual request to the LLM server."""
    load_dotenv()
    api_url = os.getenv("API_URL")
    llm_server_type = os.getenv("LLM_SERVER_TYPE", "lmstudio")
    headers = {"Content-Type": "application/json"}

    try:
        log("Thinking...")
        if llm_server_type == "lmstudio":
            lmstudio_model = os.getenv("LMSTUDIO_MODEL")
            temperature = float(os.getenv("TEMPERATURE", "0.8"))
            max_tokens = int(os.getenv("MAX_TOKENS", "4000"))
            payload = {
                "messages": data["messages"],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "model": lmstudio_model,
            }
            response = requests.post(api_url, headers=headers, json=payload)
            response_data = response.json()

            if "error" in response_data:
                log(f"Error from LMStudio: {response_data['error']}")
                return None

            save_debug(payload, response)
            return response

        elif llm_server_type == "ollama":
            ollama_model = os.getenv("OLLAMA_MODEL", "default")
            payload = {
                "prompt": data["messages"][-1]["content"],
                "model": ollama_model,
                "stream": False,
            }
            response = requests.post(api_url, headers=headers, json=payload)
            save_debug(payload, response)

            if response.status_code != 200:
                log(f"Error from Ollama: {response.status_code}")
                return None

            return response

        elif llm_server_type == "oobabooga":
            temperature = float(os.getenv("TEMPERATURE", "0.7"))
            max_tokens = int(os.getenv("MAX_TOKENS", "2000"))
            payload = {
                "messages": data["messages"],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            response = requests.post(api_url, headers=headers, json=payload)
            save_debug(payload, response)

            if response.status_code != 200:
                log(f"Error from Oobabooga: {response.status_code}")
                return None

            return response

        else:
            log(f"Unknown LLM server type: {llm_server_type}")
            return None

    except Exception as e:
        log(f"Error sending request: {str(e)}")
        debug_log(traceback.format_exc())
        return None


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

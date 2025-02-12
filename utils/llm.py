import requests
from utils.log import log
import think.memory as memory
import os
from dotenv import load_dotenv


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
            # Assuming lmstudio uses the OpenAI API format
            payload = {
                "messages": data["messages"],
                "temperature": float(data["temperature"]),
                "max_tokens": int(data["max_tokens"]),
            }
            log(f"Payload: {payload}")
            response = requests.post(api_url, headers=headers, json=payload)
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
            if response.status_code != 200:
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
        else:
            log(f"Payload: {data}")
            response = requests.post(api_url, headers=headers, json=data)
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

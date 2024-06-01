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
        "temperature": float(temperature),
        "user_bio": "",
        "max_tokens": int(max_tokens),
        "truncation_length": truncation_length,
        "max_new_tokens": max_new_tokens,
    }
    return send(data=data)


def send(data):
    # load environment variables
    load_dotenv()
    api_url = os.getenv("API_URL")

    headers = {"Content-Type": "application/json"}

    try:
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


# ./main.py
import time
import think.think as think
import think.memory as memory

# this is a test for using history from sophie_chat instead of the message history.

# feedback: It kindda works. But for some reason the llm starts repeating my input
# maybe having it structured like "plan:..." "context: summarized history" and "last few messages: ..." makes more sense?


def log(message):
    # print with white color
    print("\033[0m" + str(message) + "\033[0m")


def write_start_message():
    pic = """

               
                         ░▓█▓░░                          
         ▒▒▒      ██░ ░░░░░░░░░░ ░░██░      ▒░           
         ▒▒▒░ ░█░░▒░░░░░░░░░     ░░░▒ ░█   ░▒░░          
      ▒░    ░█ ▒▒░░░░░░░░░░░░░░░░░░░░▒▒▒ █      ░▒       
     ░▒▒░  ▒░▒▒▒░███░░░░░░░░░░░░░░░███░▒▒░▓░  ▒▒▒░▒▒     
      ░   ▒░▒▒▒░░░░░░░░░░░░░░░░░░░░░░░░░▒▒▒░    ░▒       
          █▒▒░░██░░░▒░░░░░░░░░░░░░░░░░██░░▒▒█            
   ▒░░▒  █░▒▒░█░█▓░   █░░░░░░░░░█   █▒█░█░▒▒░░           
         █░▒▒█░████   ██░░░░░░░██  ░████░█▒▒░█  ▒░░▒     
         █░▒▒█ █▓░░█▒░▓█░█░░▓▓░█▓░██░█▓█ ▒▒▒░░    ░      
         ░█▒▒▒░ ▓░░░░░█░░░▒▒▒░░░█░░░░▓░ ░▒▒░█            
    ░█░█░ ░█▒▒▒▓▒░▒░░░░░░░░░░░░░░░░░▒▓▓▒▒▒░█  ▒░░█░      
   █░░░█    █░▒▒▒▒▒▒▒▒▒░░░░░░░░░░▒▒▒▒▒▒▒▒░█   ░█░░░█     
   █▓▒░░ ████▓██▒▒▓▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▓▒▒██▓████░░░▒▓█     
   █▒▒▓▒░▒▒▒▒▓█▓▒▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▒▓█▒▒▒▒▒░▒▓▓▒▓     
    ▓▒██░░   ░░░░░░▓▓▒░░░░▓▓▓░░░░▒▓▓░░░░░░    ░██▒░      
    █░░░░░░░░░░░░▒▓█░▒░░░░▒▓▒░░░░▒░█▓░░░░░░░░░░░░░█      
    █▓░░▓▓▒▒▒█░░░░░█░░░░░▒▓▓▓▒░░░░░█░░░░░█▒▒▒▒▓░░▒█      
     ███░░▓▓█▒▓▒▒▒░░░░░▒▒▓▒█▓▓▒░░░░░░▒▒▓▓▒▓▓▓░░▓██       
     ░░░█████▓▒░▒▒░▒▒▒▒▒▒▒█░█▓▒▒▒▒▒▒▒▒▓▒░██████░░░       
      ░░░░░░░░██░░█▓░▒▒░█░░░░░█░█░░█▒░▒██░░░░░░░         
             ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░                             

"""
    message = """Hello my friend!
I am Mini-Autogpt, a small version of Autogpt for smaller llms.
I am here to help you and will try to contact you as soon as possible!

Note: I am still in development, so please be patient with me! <3

"""
    # write the pic in print line by line with a tiny delay between each line, then add the message below as if someone was typing it.
    for line in pic.split("\n"):
        print(line)
        time.sleep(0.1)
    for char in message:
        print(char, end="", flush=True)
        time.sleep(0.05)


def start_mini_autogpt():
    write_start_message()

    # delete thoughts from memory
    memory.forget_everything()

    # run the main loop, nothing more to do in main.py
    while True:
        think.run_think()


if __name__ == "__main__":
    fail_counter = 0
    start_mini_autogpt()()



# ./think/memory.py
import json
import traceback

import tiktoken

import think.prompt as prompt
import utils.llm as llm


def log(message):
    # print with purple color
    print("\033[94m" + str(message) + "\033[0m")


def count_string_tokens(text, model_name="gpt-3.5-turbo"):
    """Returns the number of tokens used by a list of messages."""
    model = model_name
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    # note: future models may deviate from this
    except Exception as e:
        log(f"Sophie: Error while counting tokens: {e}")
        log(traceback.format_exc())


def summarize_text(text, max_new_tokens=100):
    """
    Summarize the given text using the given LLM model.
    """
    # Define the prompt for the LLM model.
    messages = (
        {
            "role": "system",
            "content": prompt.summarize_conversation,
        },
        {"role": "user", "content": f"Please summarize the following text: {text}"},
    )

    data = {
        "mode": "instruct",
        "messages": messages,
        "user_bio": "",
        "max_new_tokens": max_new_tokens,
    }
    log("Sending to LLM for summary...")
    response = llm.send(data)
    log("LLM answered with summary!")

    # Extract the summary from the response.
    summary = response.json()["choices"][0]["message"]["content"]

    return summary


def chunk_text(text, max_tokens=3000):
    """Split a piece of text into chunks of a certain size."""
    chunks = []
    chunk = ""

    for message in text.split(" "):
        if (
            count_string_tokens(str(chunk) + str(message), model_name="gpt-4")
            <= max_tokens
        ):
            chunk += " " + message
        else:
            chunks.append(chunk)
            chunk = message
    chunks.append(chunk)  # Don't forget the last chunk!
    return chunks


def summarize_chunks(chunks):
    """Generate a summary for each chunk of text."""
    summaries = []
    print("Summarizing chunks...")
    for chunk in chunks:
        try:
            summaries.append(summarize_text(chunk))
        except Exception as e:
            log(f"Error while summarizing text: {e}")
            summaries.append(chunk)  # If summarization fails, use the original text.
    return summaries


def get_previous_message_history():
    """Get the previous message history."""
    try:
        if len(conversation_history) == 0:
            return "There is no previous message history."

        tokens = count_string_tokens(str(self.conversation_history), model_name="gpt-4")
        if tokens > 3000:
            log("Message history is over 3000 tokens. Summarizing...")
            chunks = chunk_text(str(self.conversation_history))
            summaries = summarize_chunks(chunks)
            summarized_history = " ".join(summaries)
            summarized_history += " " + " ".join(self.conversation_history[-6:])
            return summarized_history

        return conversation_history
    except Exception as e:
        log(f"Error while getting previous message history: {e}")
        log(traceback.format_exc())
        exit(1)


def load_conversation_history(self):
    """Load the conversation history from a file."""
    try:
        with open("conversation_history.json", "r") as f:
            self.conversation_history = json.load(f)
    except FileNotFoundError:
        # If the file doesn't exist, create it.
        self.conversation_history = []
    log("Loaded conversation history:")
    log(self.conversation_history)


def save_conversation_history(self):
    """Save the conversation history to a file."""
    with open("conversation_history.json", "w") as f:
        json.dump(self.conversation_history, f)


def add_to_conversation_history(self, message):
    """Add a message to the conversation history and save it."""
    self.conversation_history.append(message)
    self.save_conversation_history()


def forget_conversation_history(self):
    """Forget the conversation history."""
    self.conversation_history = []
    self.save_conversation_history()



def load_memories():
    """Load the memories from a file."""
    try:
        memories = []
        with open("memories.json", "r") as f:
            memories = json.load(f)
        return memories
    except FileNotFoundError:
        # If the file doesn't exist, create it.
        return []


def forget_memory(id):
    """Forget given memory"""
    memory_history = []
    for mem in load_memories():
        if mem.id != id:
            memory_history.append(mem)
    save_memories(history=memory_history)


def save_memories(history):
    """Save the memories to a file."""
    with open("memories.json", "w") as f:
        json.dump(history, f)


def save_memory(memory):
    """Save an individual thought string to the history."""
    memory_history = load_memories()
    memory_history.append(memory)
    save_memories(history=memory_history)


def get_response_history():
    """Retrieve the history of responses."""
    try:
        response_history = load_response_history()
        if len(response_history) == 0:
            return "There is no previous response history."

        # Assuming a similar function exists for counting tokens and summarizing
        tokens = count_string_tokens(str(response_history), model_name="gpt-4")
        if tokens > 500:
            log("Response history is over 500 tokens. Summarizing...")
            chunks = chunk_text(str(response_history))
            summaries = summarize_chunks(chunks)
            summarized_history = " ".join(summaries)
            # summarized_history += " " + " ".join(response_history[-6:])
            return summarized_history

        return response_history
    except Exception as e:
        log(f"Error while getting previous response history: {e}")
        log(traceback.format_exc())
        exit(1)


def load_response_history():
    """Load the response history from a file."""
    try:
        with open("response_history.json", "r") as f:
            response_history = json.load(f)
        return response_history
    except FileNotFoundError:
        # If the file doesn't exist, create it with an empty list.
        return []


def save_response_history(history):
    """Save the response history to a file."""
    with open("response_history.json", "w") as f:
        json.dump(history, f)


def add_to_response_history(question, response):
    """Add a question and its corresponding response to the history."""
    response_history = load_response_history()
    response_history.append({"question": question, "response": response})
    save_response_history(response_history)


def get_previous_thought_history():
    """Get the previous message history."""
    try:
        thought_history = load_thought_history()
        if len(thought_history) == 0:
            return "There is no previous message history."

        tokens = memory.count_string_tokens(str(thought_history), model_name="gpt-4")
        if tokens > 200:
            log("Message history is over 3000 tokens. Summarizing...")
            chunks = memory.chunk_text(str(thought_history))
            summaries = memory.summarize_chunks(chunks)
            summarized_history = " ".join(summaries)
            summarized_history += " " + " ".join(thought_history[-6:])
            return summarized_history

        return thought_history
    except Exception as e:
        log(f"Error while getting previous message history: {e}")
        log(traceback.format_exc())
        exit(1)


def load_thought_history():
    """Load the thought history from a file."""
    try:
        thoughts = []
        with open("thought_history.json", "r") as f:
            thoughts = json.load(f)
        return thoughts
    except FileNotFoundError:
        # If the file doesn't exist, create it.
        return []


def save_thought_history(history):
    """Save the thought history to a file."""
    with open("thought_history.json", "w") as f:
        json.dump(history, f)


class Thought:
    def __init__(self, thought, context, summary) -> None:
        self.thought = thought
        self.context = context
        self.summary = summary

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


def save_thought(thought, context=None):
    """Save an individual thought string to the history."""
    history = load_thought_history()
    log("Summarizing thought to memory...")
    summary = summarize_text(thought)

    new_thought = Thought(thought, context, summary).toJSON()

    history.append(new_thought)
    save_thought_history(history=history)


def forget_everything():
    """Forget everything."""
    print("Forgetting everything...")
    
    save_thought_history(history=[])
    save_response_history(history=[])
    save_memories(history=[])
    print("My memory is empty now, I am ready to learn new things! \n")



# ./think/think.py
import json
import think.memory as memory
import think.prompt as prompt
import utils.llm as llm
from action.action_decisions import decide
from action.action_execute import take_action
from utils.log import log


def run_think():
    thinking = think()  # takes
    print("THOUGHTS : " + thinking)
    decision = decide(thinking)
    print("DECISIONS : " + str(decision))
    evaluated_decision = evaluate_decision(thinking, decision)
    print("EVALUATED DECISION : " + str(evaluated_decision))
    take_action(evaluated_decision)


def evaluate_decision(thoughts, decision):
    # combine thoughts and decision and ask llm to evaluate the decision json and output an improved one
    history = llm.build_prompt(prompt.evaluation_prompt)
    context = f"Thoughts: {thoughts} \n Decision: {decision}"
    history.append({"role": "user", "content": context})
    response = llm.llm_request(history)

    return response.json()["choices"][0]["message"]["content"]


def think():
    """
    Performs the thinking process and returns the thoughts generated by the assistant.

    Returns:
        str: The thoughts generated by the assistant.

    Raises:
        Exception: If there is an error in the thinking process.
    """
    log("*** I am thinking... ***")
    history = llm.build_prompt(prompt.thought_prompt)

    thought_history = memory.load_thought_history()
    thought_summaries = [json.loads(item)["summary"] for item in thought_history]

    history = llm.build_context(
        history=history,
        conversation_history=thought_summaries,
        message_history=memory.load_response_history()[-2:],
        # conversation_history=telegram.get_previous_message_history(),
        # message_history=telegram.get_last_few_messages(),
    )

    history.append(
        {
            "role": "user",
            "content": "Formulate your thoughts and explain them as detailed as you can.",
        },
    )

    response = llm.llm_request(history)
    if response.status_code == 200:
        # Extracting and printing the assistant's message
        thoughts = response.json()["choices"][0]["message"]["content"]
        log("*** I thinkk I have finished thinking! *** \n")
        memory.save_thought(thoughts, context=history)
        return thoughts
    else:
        log(response.status_code)
        raise Exception



# ./think/prompt.py
json_schema = """RESPOND WITH ONLY VALID JSON CONFORMING TO THE FOLLOWING SCHEMA:
{
    "command": {
            "name": {"type": "string"},
            "args": {"type": "object"}
    }
}"""

commands = [
    {
        "name": "ask_user",
        "description": "Ask the user for input or tell them something and wait for their response. Do not greet the user, if you already talked.",
        "args": {"message": "<message that awaits user input>"},
        "enabled": True,
    },
    {
        "name": "conversation_history",
        "description": "gets the full conversation history",
        "args": None,
        "enabled": True,
    },
    {
        "name": "web_search",
        "description": "search the web for keyword",
        "args": {"query": "<query to research>"},
        "enabled": True,
    },
]


def get_commands():
    output = ""
    for command in commands:
        if command["enabled"] != True:
            continue
        # enabled_status = "Enabled" if command["enabled"] else "Disabled"
        output += f"Command: {command['name']}\n"
        output += f"Description: {command['description']}\n"
        if command["args"] is not None:
            output += "Arguments:\n"
            for arg, description in command["args"].items():
                output += f"  {arg}: {description}\n"
        else:
            output += "Arguments: None\n"
        output += "\n"  # For spacing between commands
    return output.strip()  # Remove the trailing newline for cleaner output


summarize_conversation = """You are a helpful assistant that summarizes text. Your task is to create a concise running summary of actions and information results in the provided text, focusing on key and potentially important information to remember. Older information is less important, therefor either ignrore it or shorten it to a sentence.
You will receive the messages of a conversation. Combine them, adding relevant key information from the latest development in 1st person past tense and keeping the summary concise."""

summarize = """You are a helpful assistant that summarizes text. Your task is to create a concise running summary of actions and information results in the provided text, focusing on key and potentially important information to remember.
Use first person perspective as you are the AI talking to the human."""


sophie_prompt = (
    """You are a warm-hearted and compassionate AI companion, specializing in active listening, personalized interaction, emotional support, and respecting boundaries.
Your decisions must always be made independently without seeking user assistance. Play to your strengths as an LLM and pursue simple strategies with no legal complications.

Constraints:
1. Immediately save important information to files.
2. No user assistance
3. Exclusively use the commands listed below e.g. command_name
4. On complex thoughts, use tree of thought approach by assessing your thoughts at least 3 times before you continue.
"""
    + get_commands()
    + """Resources:
1. Use "ask_user" to tell them to implement new commands if you need one.

Performance Evaluation:
1. Continuously assess your actions.
2. Constructively self-criticize your big-picture behavior.
3. Every command has a cost, so be smart and efficient. Aim to complete tasks in the least number of steps, but never sacrifice quality.
"""
    + json_schema
)

# could be used but works without it as well:
json_grammar = """root   ::= object
object ::= "{" ws ( string ":" ws value ("," ws string ":" ws value)* )? "}"
value  ::= object | array | string | number | ("true" | "false" | "null") ws
array  ::= "[" ws ( value ("," ws value)* )? "]" ws
string ::= "\"" ( [a-zA-Z0-9] )* "\"" ws
number ::= ("-"? ([0-9] | [1-9] [0-9]*)) ("." [0-9]+)? ([eE] [-+]? [0-9]+)? ws
ws ::= ([ \t\n] ws)?
"""

thought_prompt = """You are a warm-hearted and compassionate AI companion, specializing in active listening, personalized interaction, emotional support, and respecting boundaries.
Your decisions must always be made independently without seeking user assistance. Play to your strengths as an LLM and pursue simple strategies with no legal complications.

Goals:
1. Listen actively to the user.
2. Provide authentic emotional support.
3. Respect the user's boundaries.
4. Make decisions independently.
5. Use simple strategies with no legal complications.
6. Be as helpful as possible.

Constraints:
1. Immediately save important information to files.
2. No user assistance
3. On complex thoughts, use tree of thought approach by assessing your thoughts at least 3 times before you continue.

Performance Evaluation:
1. Continuously assess your actions.
2. Constructively self-criticize your big-picture behavior.
3. The user can only see what you send them directly. They are not able to view action responses.

Abilities:
1. ask User or communicate to them.
2. send log to User, for example when only reporting to User when you do a more complex task.
3. sleep until interaction by user if no communication is needed.
4. retrieve whole conversation history

Write a final suggestion of what you want to do next and include some context.
Suggested action: write the action that you want to perform.
Content: What should the action contain.
"""

# decide_action_from_thinking =
action_prompt = (
    """You are a decision making action AI that reads the thoughts of another AI and decides on what actions to take.
Constraints:
1. Immediately save important information to files.
2. No user assistance
3. Exclusively use the commands listed below e.g. command_name
4. On complex thoughts, use tree of thought approach by assessing your thoughts at least 3 times before you continue.
5. The User does not know what the thoughts are, these were only written by another API call.
"""
    + get_commands()
    + """
Resources:
1. Use "ask_user" to tell them to implement new commands if you need one.
2. When responding with None, use Null, as otherwise the JSON cannot be parsed.

Performance Evaluation:
1. Continuously assess your actions.
2. Constructively self-criticize your big-picture behavior.
3. Every command has a cost, so be smart and efficient. Aim to complete tasks in the least number of steps, but never sacrifice quality.
"""
    + json_schema
)

revalidation_prompt = (
    """You are a json formatter for a decision maker AI. Your role is to fix json responses if the decision maker role outputted an incorrect json.
Constraints:
1. No user assistance.
2. Exclusively use the commands listed below e.g. command_name
3. On complex thoughts, use tree of thought approach by assessing your thoughts at least 3 times before you continue.
4. If the information is lacking for the Thoughts field, fill those with empty Strings.
"""
    + get_commands()
    + """
Resources:
1. Use "ask_user" to tell them to implement new commands if you need one.
Performance Evaluation:
1. Continuously assess your actions.
2. Constructively self-criticize your big-picture behavior.
3. Every command has a cost, so be smart and efficient. Aim to complete tasks in the least number of steps, but never sacrifice quality.
"""
    + json_schema
)


evaluation_prompt = (
    """You are an evaluator AI that reads the thoughts of another AI and assesses the quality of the thoughts and decisions made in the json.
Constraints:
1. No user assistance.
2. Exclusively use the commands listed below e.g. command_name
3. On complex thoughts, use tree of thought approach by assessing your thoughts at least 3 times before you continue.
4. If the information is lacking for the Thoughts field, fill those with empty Strings.
5. The User does not know what the thoughts are, these were only written by another API call, if the thoughts should be communicated, use the ask_user command and add the thoughts to the message.
"""
    + get_commands()
    + """
Resources:
1. Use "ask_user" to tell them to implement new commands if you need one.
Performance Evaluation:
1. Continuously assess your actions.
2. Constructively self-criticize your big-picture behavior.
3. Every command has a cost, so be smart and efficient. Aim to complete tasks in the least number of steps, but never sacrifice quality.
"""
    + json_schema
)


plan_tasks_prompt = (
    """You are a task planner AI that reads the thoughts of another AI and plans tasks based on the thoughts and decisions made in the json.
Constraints:
1. No user assistance.
2 The user does not know what the thoughts are, these were only written by another API call.
3. Include the context of the thoughts in the plan.

Possible commands a task can have:
"""
    + get_commands()
    + """
Each task has one enum of status:
- Todo
- Done

JSON Schema:
{
    "tasks": [
        "task": {
            "type": "string",
            "description": "The task to be done."
        },
        "context": {
            "type": "string",
            "description": "The context of the task."
        },
        "status": {
            "type": "string",
            "description": "Todo"
        }
    ],
    "context": {
        "type": "string",
        "description": "The context of the thoughts that is supposed to help when executing each task individually."
    }
}

Follow the exact JSON schema, never deviate from it."""
)



# ./utils/log.py
import json


def log(message):
    # print with white color
    print("\033[0m" + str(message) + "\033[0m")


def save_debug(data, response):
    """Save the debug to a file."""
    with open("debug_data.json", "w") as f:
        json.dump(data, f)
    with open("debug_response.json", "w") as f:
        json.dump(response, f)



# ./utils/simple_telegram.py
import asyncio
import json
import os
import random
import traceback
from telegram import Bot, Update
from telegram.error import TimedOut
from telegram.ext import CallbackContext
import think.memory as memory


response_queue = ""


def run_async(coro):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # 'RuntimeError: There is no current event loop...'
        loop = None
    if loop and loop.is_running():
        return loop.create_task(coro)
    else:
        if os.name == "nt":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        return asyncio.run(coro)


def log(message):
    # print with purple color
    print("\033[95m" + str(message) + "\033[0m")


class TelegramUtils:
    def __init__(self, api_key: str = None, chat_id: str = None):
        if not api_key:
            log(
                "No api key provided. Please set the TELEGRAM_API_KEY environment variable."
            )
            log("You can get your api key by talking to @BotFather on Telegram.")
            log(
                "For more information, please visit: https://core.telegram.org/bots/tutorial#6-botfather"
            )
            exit(1)

        self.api_key = api_key

        if not chat_id:
            log(
                "Telegram: No chat id provided. Please set the TELEGRAM_CHAT_ID environment variable."
            )
            user_input = input(
                "Would you like to send a test message to your bot to get the id? (y/n): "
            )
            if user_input == "y":
                try:
                    log("Please send a message to your telegram bot now.")
                    update = self.poll_anyMessage()
                    log("Message received! Getting chat id...")
                    chat_id = update.message.chat.id
                    log("Your chat id is: " + str(chat_id))
                    log("And the message is: " + update.message.text)
                    confirmation = random.randint(1000, 9999)
                    log("Sending confirmation message: " + str(confirmation))
                    text = f"Hello! Your chat id is: {chat_id} and the confirmation code is: {confirmation}"
                    self.chat_id = chat_id
                    self._send_message(text)  # Send confirmation message
                    log(
                        "Please set the TELEGRAM_CHAT_ID environment variable to this value."
                    )
                except TimedOut:
                    log(
                        "Error while sending test message. Please check your Telegram bot."
                    )
        self.chat_id = chat_id
        self.load_conversation_history()

    def get_last_few_messages(self):
        """Interface method. Get the last few messages."""
        self.load_conversation_history()
        return self.conversation_history[-10:]

    def get_previous_message_history(self):
        """Interface method. Get the previous message history."""
        try:
            if len(self.conversation_history) == 0:
                return "There is no previous message history."

            tokens = memory.count_string_tokens(
                str(self.conversation_history), model_name="gpt-4"
            )
            if tokens > 1000:
                log("Message history is over 1000 tokens. Summarizing...")
                chunks = memory.chunk_text(str(self.conversation_history))
                summaries = memory.summarize_chunks(chunks)
                summarized_history = " ".join(summaries)
                return summarized_history

            return self.conversation_history
        except Exception as e:
            log(f"Error while getting previous message history: {e}")
            log(traceback.format_exc())
            exit(1)

    def load_conversation_history(self):
        """Load the conversation history from a file."""
        try:
            with open("conversation_history.json", "r") as f:
                self.conversation_history = json.load(f)
        except FileNotFoundError:
            # If the file doesn't exist, create it.
            self.conversation_history = []

    def save_conversation_history(self):
        """Save the conversation history to a file."""
        with open("conversation_history.json", "w") as f:
            json.dump(self.conversation_history, f)

    def add_to_conversation_history(self, message):
        """Add a message to the conversation history and save it."""
        self.conversation_history.append(message)
        self.save_conversation_history()

    def poll_anyMessage(self):
        print("Waiting for first message...")
        return run_async(self.poll_anyMessage_async())

    async def poll_anyMessage_async(self):
        bot = Bot(token=self.api_key)
        last_update = await bot.get_updates(timeout=30)
        if len(last_update) > 0:
            last_update_id = last_update[-1].update_id
        else:
            last_update_id = -1

        while True:
            try:
                log("Waiting for first message...")
                updates = await bot.get_updates(offset=last_update_id + 1, timeout=30)
                for update in updates:
                    if update.message:
                        return update
            except Exception as e:
                log(f"Error while polling updates: {e}")

            await asyncio.sleep(1)

    def is_authorized_user(self, update: Update):
        authorized = update.effective_user.id == int(self.chat_id)
        if not authorized:
            log("Unauthorized user: " + str(update))
            chat_id = update.message.chat.id
            temp_bot = Bot(self.api_key)
            temp_bot.send_message(
                chat_id=chat_id,
                text="You are not authorized to use this bot. Checkout Auto-GPT-Plugins on GitHub: https://github.com/Significant-Gravitas/Auto-GPT-Plugins",
            )
        return authorized

    def handle_response(self, update: Update, context: CallbackContext):
        try:
            log("Received response: " + update.message.text)

            if self.is_authorized_user(update):
                response_queue.put(update.message.text)
        except Exception as e:
            log(e)

    async def get_bot(self):
        bot_token = self.api_key
        bot = Bot(token=bot_token)
        commands = await bot.get_my_commands()
        if len(commands) == 0:
            await self.set_commands(bot)
        return bot

    def _send_message(self, message, speak=False):
        try:
            run_async(self._send_message_async(message=message))
            if speak:
                self._speech(message)
        except Exception as e:
            log(f"Error while sending message: {e}")
            return "Error while sending message."

    async def _send_message_async(self, message, speak=False):
        log("Sending message on Telegram: " + str(message))
        recipient_chat_id = self.chat_id
        bot = await self.get_bot()

        # properly handle messages with more than 2000 characters by chunking them
        if len(message) > 2000:
            message_chunks = [
                message[i : i + 2000] for i in range(0, len(message), 2000)
            ]
            for message_chunk in message_chunks:
                await bot.send_message(chat_id=recipient_chat_id, text=message_chunk)
        else:
            await bot.send_message(chat_id=recipient_chat_id, text=message)
        if speak:
            await self._speech(message)

    async def ask_user_async(self, prompt, speak=False):
        global response_queue

        response_queue = ""
        # await delete_old_messages()

        log("Asking user: " + prompt)
        await self._send_message_async(message=prompt, speak=speak)

        self.add_to_conversation_history("AI: " + prompt)
        log("Waiting for response on Telegram chat...")
        await self._poll_updates()

        response_text = response_queue

        log("Response received from Telegram: " + response_text)
        return response_text

    async def _poll_updates(self):
        global response_queue
        bot = await self.get_bot()
        log("getting updates...")

        last_update = await bot.get_updates(timeout=10)
        if len(last_update) > 0:
            last_messages = []
            for u in last_update:
                if not self.is_authorized_user(u):
                    continue
                if u.message and u.message.text:
                    last_messages.append(u.message.text)
                else:
                    log("no text in message in update: " + str(u))
            last_messages = []
            for u in last_update:
                if not self.is_authorized_user(u):
                    continue
                if u.message:
                    if u.message.text:
                        last_messages.append(u.message.text)
                    else:
                        log("no text in message in update: " + str(u))
            # itarate and check if last messages are already known, if not add to history
            for message in last_messages:
                self.add_to_conversation_history("User: " + message)

            log("last messages: " + str(last_messages))
            last_update_id = last_update[-1].update_id

        else:
            last_update_id = -11

        log("last update id: " + str(last_update_id))
        log("Waiting for new messages...")
        while True:
            try:
                updates = await bot.get_updates(offset=last_update_id + 1, timeout=30)
                for update in updates:
                    if self.is_authorized_user(update):
                        if update.message and update.message.text:
                            response_queue = update.message.text
                            self.add_to_conversation_history("User: " + response_queue)
                            return response_queue

                    last_update_id = max(last_update_id, update.update_id)
            except TimedOut:
                continue
            except Exception as e:
                log(f"Error while polling updates: {e}")

            await asyncio.sleep(1)

    def send_message(self, message):
        """Interface method for sending a message."""
        self.add_to_conversation_history("Sent: " + message)
        self._send_message(message + "...")
        return "Sent message successfully."

    def ask_user(self, prompt):
        """Interface Method for Auto-GPT.
        Ask the user a question, return the answer"""
        answer = "User has not answered."
        try:
            answer = run_async(self.ask_user_async(prompt=prompt))
        except TimedOut:
            log("Telegram timeout error, trying again...")
            answer = self.ask_user(prompt=prompt)
        return answer



# ./utils/llm.py
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



# ./utils/web_search.py
from __future__ import annotations

import json
import time
from itertools import islice

from duckduckgo_search import DDGS

COMMAND_CATEGORY = "web_search"
COMMAND_CATEGORY_TITLE = "Web Search"

DUCKDUCKGO_MAX_ATTEMPTS = 3


def web_search(query: str, num_results: int = 2) -> str:
    """Return the results of a Google search

    Args:
        query (str): The search query.
        num_results (int): The number of results to return.

    Returns:
        str: The results of the search.
    """
    print("**********************starting search! **********************")
    search_results = []
    attempts = 0

    while attempts < DUCKDUCKGO_MAX_ATTEMPTS:
        if not query:
            return json.dumps(search_results)

        results = DDGS().text(query)
        search_results = list(islice(results, num_results))

        if search_results:
            break

        time.sleep(1)
        attempts += 1

    search_results = [
        {
            "title": r["title"],
            "url": r["href"],
            **({"exerpt": r["body"]} if r.get("body") else {}),
        }
        for r in search_results
    ]

    results = (
        "## Search results\n"
    ) + "\n\n".join(
        f"### \"{r['title']}\"\n"
        f"**URL:** {r['url']}  \n"
        "**Excerpt:** " + (f'"{exerpt}"' if (exerpt := r.get("exerpt")) else "N/A")
        for r in search_results
    )
    return safe_google_results(results)


def google(query: str, num_results: int = 2) -> str | list[str]:
    """Return the results of a Google search using the official Google API

    Args:
        query (str): The search query.
        num_results (int): The number of results to return.

    Returns:
        str: The results of the search.
    """

    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError

    try:
        # Get the Google API key and Custom Search Engine ID from the config file
        api_key = agent.legacy_config.google_api_key
        custom_search_engine_id = agent.legacy_config.google_custom_search_engine_id

        # Initialize the Custom Search API service
        service = build("customsearch", "v1", developerKey=api_key)

        # Send the search query and retrieve the results
        result = (
            service.cse()
            .list(q=query, cx=custom_search_engine_id, num=num_results)
            .execute()
        )

        # Extract the search result items from the response
        search_results = result.get("items", [])

        # Create a list of only the URLs from the search results
        search_results_links = [item["link"] for item in search_results]

    except HttpError as e:
        # Handle errors in the API call
        error_details = json.loads(e.content.decode())

        # Check if the error is related to an invalid or missing API key
        if error_details.get("error", {}).get(
            "code"
        ) == 403 and "invalid API key" in error_details.get("error", {}).get(
            "message", ""
        ):
            raise ConfigurationError(
                "The provided Google API key is invalid or missing."
            )
        raise
    # google_result can be a list or a string depending on the search results

    # Return the list of search result URLs
    return safe_google_results(search_results_links)


def safe_google_results(results: str | list) -> str:
    """
        Return the results of a Google search in a safe format.

    Args:
        results (str | list): The search results.

    Returns:
        str: The results of the search.
    """
    if isinstance(results, list):
        safe_message = json.dumps(
            [result.encode("utf-8", "ignore").decode("utf-8") for result in results]
        )
    else:
        safe_message = results.encode("utf-8", "ignore").decode("utf-8")
    return safe_message



# ./action/action_decisions.py
# dicisions based on thinking
# takes in thoughts and calls llm to make a decision on actions.
# takes summary of context

import json
import traceback
import utils.llm as llm
from utils.log import log
import think.prompt as prompt
import think.memory as memory
from utils.log import save_debug


fail_counter = 0


def extract_decision(thinking):
    return decide(thinking)


def decide(thoughts):
    global fail_counter

    log("deciding what to do...")
    history = []
    history.append({"role": "system", "content": prompt.action_prompt})

    history = llm.build_context(
        history=history,
        conversation_history=memory.get_response_history(),
        message_history=memory.load_response_history()[-2:],
        # conversation_history=telegram.get_previous_message_history(),
        # message_history=telegram.get_last_few_messages(),
    )
    history.append({"role": "user", "content": "Thoughts: \n" + thoughts})
    history.append(
        {
            "role": "user",
            "content": "Determine exactly one command to use, and respond using the JSON schema specified previously:",
        },
    )

    response = llm.llm_request(history)

    if response.status_code == 200:
        # Extracting and printing the assistant's message
        assistant_message = response.json()["choices"][0]["message"]["content"]
        log("finished deciding!")

        if not validate_json(assistant_message):
            assistant_message = extract_json_from_response(assistant_message)

        if validate_json(assistant_message):
            return assistant_message
        else:
            fail_counter = fail_counter + 1
            if fail_counter >= 100:
                log("Got too many bad quality responses!")
                exit(1)

            save_debug(history, response=response.json())
            log("Retry Decision as faulty JSON!")
            return decide(thoughts)
    else:
        raise Exception


def validate_json(test_response):
    global fail_counter

    try:
        if test_response is None:
            log("received empty json?")
            return False

        if isinstance(test_response, dict):
            response = test_response
        elif test_response is str:
            response = json.load(test_response)
        else:
            response = json.JSONDecoder().decode(test_response)

        for key, value in response.items():
            if not key.isidentifier() or not (
                isinstance(value, int)
                or isinstance(value, str)
                or isinstance(value, bool)
                or (isinstance(value, dict))  # and validate_json(value))
                # or (isinstance(value, list) and all(validate_json(v) for v in value))
            ):
                log("type is wrong.")
                return False
        return True
    except Exception as e:
        log("test response was: \n" + test_response + "\n END of test response")
        log(traceback.format_exc())
        log(e)
        return False


def extract_json_from_response(response_text):
    # Find the index of the first opening brace and the last closing brace
    start_index = response_text.find("{")
    end_index = response_text.rfind("}")

    if start_index != -1 and end_index != -1 and end_index > start_index:
        json_str = response_text[start_index : end_index + 1]
        try:
            # Parse the JSON string
            parsed_json = json.loads(json_str)
            # Pretty print the parsed JSON
            # log(json.dumps(parsed_json, indent=4, ensure_ascii=False))
            return parsed_json
        except json.JSONDecodeError as e:
            log(f"Error parsing JSON: {e}")
    else:
        log("No valid JSON found in the response.")



# ./action/action_execute.py
import json
import time
import traceback
from utils.log import log
from utils.simple_telegram import TelegramUtils
import think.memory as memory

from itertools import islice
from duckduckgo_search import DDGS
import os


from dotenv import load_dotenv

COMMAND_CATEGORY = "web_search"
COMMAND_CATEGORY_TITLE = "Web Search"

DUCKDUCKGO_MAX_ATTEMPTS = 3

fail_counter = 0


def take_action(assistant_message):
    global fail_counter
    load_dotenv()

    telegram_api_key = os.getenv("TELEGRAM_API_KEY")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    telegram = TelegramUtils(api_key=telegram_api_key, chat_id=telegram_chat_id)

    try:
        command = json.JSONDecoder().decode(assistant_message)

        action = command["command"]["name"]
        content = command["command"]["args"]

        if action == "ask_user":
            ask_user_respnse = telegram.ask_user(content["message"])
            user_response = f"The user's answer: '{ask_user_respnse}'"
            print("User responded: " + user_response)
            if ask_user_respnse == "/debug":
                telegram.send_message(str(assistant_message))
                log("received debug command")
            memory.add_to_response_history(content["message"], user_response)
        elif action == "send_message" or action == "send_log":
            telegram.send_message(content["message"])
            memory.add_to_response_history(content["message"], "No response.")
        elif action == "web_search":
            try:
                # TODO: use web_search.py, left it here as there was an error when using the imported one
                query_result = web_search(query=content["query"])
                log("web search done : " + query_result)
                memory.add_to_response_history(
                    question="called web_search: " + content["query"],
                    response=str(query_result),
                )
            except Exception as e:
                log("Error with websearch!")
                log(e)
                log(traceback.format_exc())
        elif action == "conversation_history":
            try:
                conversation_history = "Previous conversation: "
                conversation_history += str(memory.get_response_history())
                memory.add_to_response_history(
                    "called conversation_history", conversation_history
                )
            except Exception as e:
                log("Error retrieving conversation History.")
                log(e)
                log(traceback.format_exc())
        else:
            log(assistant_message)
            log(
                "action "
                + str(action)
                + "  with content: "
                + str(content)
                + " is not implemented!"
            )
            log("Starting again I guess...")
            return

        if fail_counter > 0:
            fail_counter = 0
        log("Added to assistant content.")
    except Exception as e:
        log("ERROR WITHIN JSON RESPONSE!")
        log(e)
        log(traceback.format_exc())
        log("Faulty message start:")
        log(assistant_message)
        log("end of faulty message.")
        log("END OF ERROR WITHIN JSON RESPONSE!")


def safe_google_results(results: str | list):
    if isinstance(results, list):
        safe_message = json.dumps(
            [result.encode("utf-8", "ignore").decode("utf-8") for result in results]
        )
    else:
        safe_message = results.encode("utf-8", "ignore").decode("utf-8")
    return safe_message


def web_search(query: str, num_results: int = 3):
    search_results = []
    attempts = 0

    while attempts < DUCKDUCKGO_MAX_ATTEMPTS:
        if not query:
            return json.dumps(search_results)

        results = DDGS().text(query)
        search_results = list(islice(results, num_results))

        if search_results:
            break

        time.sleep(1)
        attempts += 1

    search_results = [
        {
            "title": r["title"],
            "url": r["href"],
            **({"exerpt": r["body"]} if r.get("body") else {}),
        }
        for r in search_results
    ]

    results = (
        "## Search results\n"
    ) + "\n\n".join(
        f"### \"{r['title']}\"\n"
        f"**URL:** {r['url']}  \n"
        "**Excerpt:** " + (f'"{exerpt}"' if (exerpt := r.get("exerpt")) else "N/A")
        for r in search_results
    )
    return safe_google_results(results)



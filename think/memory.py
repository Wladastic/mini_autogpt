import json
import traceback

import think.prompt as prompt
import utils.llm as llm


def log(message):
    # print with purple color
    print("\033[94m" + str(message) + "\033[0m")


def count_string_tokens(text, model_name="gpt-3.5-turbo"):
    """Returns the number of tokens used by a list of messages."""
    # Approximate token count using character count divided by 4 (average characters per token)
    return len(text) // 4


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

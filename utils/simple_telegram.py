import asyncio
import json
import os
import random
import traceback
from telegram import Bot, Update
from telegram.error import TimedOut
from telegram.ext import CallbackContext
import think.memory as memory
from utils.log import log

response_queue = ""
telegram_utils = None

def test_init():
    """Initialize the Telegram bot with environment variables."""
    global telegram_utils

    # Ensure both values are provided and not default template values
    api_key = os.getenv("TELEGRAM_API_KEY")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not api_key or api_key == "your_telegram_api_key":
        raise ValueError("Telegram API key not configured. Please edit .env file.")
    if not chat_id or chat_id == "your_telegram_chat_id":
        raise ValueError("Telegram chat ID not configured. Please edit .env file.")

    telegram_utils = TelegramUtils(api_key=api_key, chat_id=chat_id, test_mode=True)

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

class TelegramUtils:
    def __init__(self, api_key: str = None, chat_id: str = None, test_mode: bool = False):
        if not api_key:
            raise ValueError(
                "No API key provided. Please set the TELEGRAM_API_KEY environment variable. "
                "You can get your API key by talking to @BotFather on Telegram. "
                "For more information, visit: https://core.telegram.org/bots/tutorial#6-botfather"
            )

        self.api_key = api_key

        if not chat_id:
            log("No chat id provided. Please set the TELEGRAM_CHAT_ID environment variable.")
            user_input = input("Would you like to send a test message to your bot to get the id? (y/n): ")
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
                    log("Please set the TELEGRAM_CHAT_ID environment variable to this value.")
                except TimedOut:
                    raise RuntimeError("Error while sending test message. Please check your Telegram bot.")
            else:
                raise ValueError("Chat ID is required. Please set the TELEGRAM_CHAT_ID environment variable.")

        if test_mode:
            return
        
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

            tokens = memory.count_string_tokens(str(self.conversation_history), model_name="gpt-4")
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
        global response_queue
        try:
            log("Received response: " + update.message.text)
            if self.is_authorized_user(update):
                response_queue = update.message.text
        except Exception as e:
            log(e)

    async def get_bot(self):
        """Get or create a bot instance."""
        return Bot(token=self.api_key)

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
            message_chunks = [message[i:i+2000] for i in range(0, len(message), 2000)]
            for message_chunk in message_chunks:
                await bot.send_message(chat_id=recipient_chat_id, text=message_chunk)
        else:
            await bot.send_message(chat_id=recipient_chat_id, text=message)
        if speak:
            await self._speech(message)

    async def ask_user_async(self, prompt, speak=False):
        global response_queue

        response_queue = ""

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
            # iterate and check if last messages are already known, if not add to history
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

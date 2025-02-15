import os
import sys
import time
import traceback
from dotenv import load_dotenv

import think.memory as memory
import think.think as think
import utils.simple_telegram as telegram
import utils.llm as llm
from utils.log import log


def check_environment():
    """Check if the environment is properly configured."""
    print("Checking configuration...")

    # Load environment variables
    load_dotenv()
    errors = []

    # Check LLM configuration
    llm_server_type = os.getenv("LLM_SERVER_TYPE")
    if not llm_server_type:
        errors.append("LLM server type not configured. Please edit .env file.")
    elif llm_server_type not in ["lmstudio", "ollama", "oobabooga"]:
        errors.append(f"Invalid LLM server type: {llm_server_type}")
    else:
        # Test LLM connection
        error = llm.test_connection()
        if error:
            errors.append(error)

    # Initialize and test Telegram connection
    try:
        telegram.test_init()
    except Exception as e:
        errors.append(str(e))

    # If there are any errors, display them and exit
    if errors:
        print("\nConfiguration errors found:")
        for error in errors:
            print(f"- {error}")
        print("\nPlease fix these issues and try again.")
        exit(1)

    print("✅ All checks passed!")
    log("Environment check completed successfully")


def type_text(text, delay=0.02):
    """Type out text with a typing animation."""
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()


def load_logo():
    """Load the ASCII art logo from file."""
    try:
        with open("assets/logo.txt", "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        log(f"Could not load logo: {e}")
        return ""
    
def type_logo(logo, delay=0.08):
    """Type out the ASCII art logo."""
    for line in logo.split("\n"):
        type_text(line, delay=delay)


def initialize():
    """Initialize Mini-AutoGPT."""
    logo = load_logo()
    type_text(logo, delay=0.005)

    type_text("Hello my friend!")
    type_text("I am Mini-Autogpt, a small version of Autogpt for smaller llms.")
    type_text("I am here to help you and will try to contact you as soon as possible!")
    print()
    type_text("Note: I am still in development, so please be patient with me! <3")
    print()
    memory.forget_everything()


def main_loop():
    """Main loop for Mini-AutoGPT."""
    try:
        while True:
            try:
                think.run_think()
            except KeyboardInterrupt:
                # Inner loop interrupt - give chance to confirm exit
                log("\nPress Ctrl+C again to exit, or press Enter to continue...")
                try:
                    response = input()
                    log("Continuing...")
                except KeyboardInterrupt:
                    # Second interrupt - exit
                    raise KeyboardInterrupt
            except Exception as e:
                if str(e):
                    log(f"Error: {str(e)}")
                if traceback:
                    log(f"Traceback: {traceback.format_exc()}")
                log("Waiting 5 seconds before retrying...")
                time.sleep(5)

    except KeyboardInterrupt:
        # Outer loop interrupt - clean exit
        log("\nGracefully shutting down...")
        log("Thanks for using Mini-AutoGPT! Goodbye!")
        sys.exit(0)


def start_mini_autogpt():
    """Start Mini-AutoGPT."""
    # Check configuration before anything else
    check_environment()

    # Initialize and start the main loop
    initialize()
    main_loop()


if __name__ == "__main__":
    start_mini_autogpt()

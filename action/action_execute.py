import json
import time
import traceback
from utils.log import log, save_debug
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
            try:
                log("Waiting for user response...")
                ask_user_respnse = telegram.ask_user(content["message"])
                user_response = f"The user's answer: '{ask_user_respnse}'"
                print("User responded: " + user_response)
                if ask_user_respnse == "/debug":
                    telegram.send_message(str(assistant_message))
                    log("received debug command")
                save_debug(content, {"response": user_response}, request_type="user_interaction")
                memory.add_to_response_history(content["message"], user_response)
            except KeyboardInterrupt:
                # Clean up and re-raise for main loop to handle
                log("\nUser interaction interrupted...")
                raise

        elif action == "send_message" or action == "send_log":
            telegram.send_message(content["message"])
            save_debug(content, {"status": "sent"}, request_type="send_message")
            memory.add_to_response_history(content["message"], "No response.")

        elif action == "web_search":
            try:
                query_result = web_search(query=content["query"])
                log("web search done : " + query_result)
                save_debug(content, {"result": query_result}, request_type="web_search")
                memory.add_to_response_history(
                    question="called web_search: " + content["query"],
                    response=str(query_result),
                )
            except KeyboardInterrupt:
                log("\nWeb search interrupted...")
                raise
            except Exception as e:
                log("Error with websearch!")
                log(e)
                log(traceback.format_exc())

        elif action == "conversation_history":
            try:
                conversation_history = "Previous conversation: "
                conversation_history += str(memory.get_response_history())
                save_debug(content, {"history": conversation_history}, request_type="history_request")
                memory.add_to_response_history(
                    "called conversation_history", conversation_history
                )
            except KeyboardInterrupt:
                log("\nHistory retrieval interrupted...")
                raise
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
            save_debug(command, {"error": "action not implemented"}, request_type="unknown_action")
            log("Starting again I guess...")
            return

        if fail_counter > 0:
            fail_counter = 0
        log("Added to assistant content.")

    except KeyboardInterrupt:
        # Re-raise for main loop to handle
        log("\nAction interrupted...")
        raise
    except Exception as e:
        log("ERROR WITHIN JSON RESPONSE!")
        log(e)
        log(traceback.format_exc())
        log("Faulty message start:")
        log(assistant_message)
        log("end of faulty message.")
        log("END OF ERROR WITHIN JSON RESPONSE!")

def safe_google_results(results: str or list):
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

    try:
        while attempts < DUCKDUCKGO_MAX_ATTEMPTS:
            if not query:
                return json.dumps(search_results)

            try:
                results = DDGS().text(query)
                search_results = list(islice(results, num_results))

                if search_results:
                    break

                log(f"Search attempt {attempts + 1} failed, retrying...")
                time.sleep(1)
                attempts += 1

            except KeyboardInterrupt:
                log("\nSearch attempt interrupted...")
                raise
            except Exception as e:
                log(f"Search attempt failed: {e}")
                time.sleep(1)
                attempts += 1
                continue

        if not search_results:
            log("No search results found after all attempts")
            return json.dumps([{"title": "No results", "url": "", "body": "Search yielded no results"}])

        search_results = [
            {
                "title": r["title"],
                "url": r["href"],
                **({"exerpt": r["body"]} if r.get("body") else {}),
            }
            for r in search_results
        ]

        results = ("## Search results\n") + "\n\n".join(
            f"### \"{r['title']}\"\n"
            f"**URL:** {r['url']}  \n"
            "**Excerpt:** " + (f'"{exerpt}"' if (exerpt := r.get("exerpt")) else "N/A")
            for r in search_results
        )
        return safe_google_results(results)

    except KeyboardInterrupt:
        log("\nSearch process interrupted...")
        raise
    except Exception as e:
        log(f"Search process failed: {e}")
        return json.dumps([{"title": "Error", "url": "", "body": f"Search failed: {str(e)}"}])

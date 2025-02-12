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

    try:
        response = llm.llm_request(history)

        if response is None or response.status_code != 200:
            log("Invalid response from LLM")
            return None

        response_json = response.json()
        if not response_json or "choices" not in response_json:
            log("Invalid response format")
            return None

        assistant_message = response_json["choices"][0]["message"]["content"]
        log("finished deciding!")

        if not validate_json(assistant_message):
            # First try extracting JSON from the full response
            assistant_message = extract_json_from_response(assistant_message)
            if assistant_message is None:
                log("Could not extract valid JSON from response")
                return None

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
    except KeyboardInterrupt:
        exit(0)
    except Exception as e:
        log(f"Error during decision making: {str(e)}")
        log(traceback.format_exc())
        exit(1)


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

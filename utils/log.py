import os
import json
import time
from datetime import datetime


def log(message):
    """Log a message, respecting DEBUG setting."""
    debug = os.getenv("DEBUG", "false").lower() == "true"
    if debug:
        # print with purple color
        print("\033[94m" + str(message) + "\033[0m")
    else:
        # Only print messages that are essential for user feedback
        if isinstance(message, str) and any(
            keyword in message
            for keyword in [
                "Error",
                "Please",
                "Warning",
                "Success",
                "✅",
                "❌",
            ]
        ):
            print(str(message))


def save_debug(data, response, request_type="unknown"):
    """
    Save the debug data and response to files with timestamps and type labels.
    
    Args:
        data: The request data
        response: The response data
        request_type: Type of request (e.g., 'think', 'decide', 'user_response', etc.)
    """
    debug = os.getenv("DEBUG", "false").lower() == "true"
    if not debug:
        return

    try:
        # Create debug directories if they don't exist
        os.makedirs("debug/history", exist_ok=True)
        os.makedirs("debug", exist_ok=True)

        # Get current timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        # Create debug entry with metadata
        debug_entry = {
            "timestamp": timestamp,
            "timestamp_readable": datetime.now().isoformat(),
            "request_type": request_type,
            "request": data
        }

        # Convert response to JSON-serializable format
        if hasattr(response, "json"):
            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}
        else:
            response_data = response

        debug_entry["response"] = response_data

        # Save timestamped and typed debug file
        debug_file = f"debug/history/debug_{timestamp}_{request_type}.json"
        with open(debug_file, "w", encoding="utf-8") as f:
            json.dump(debug_entry, f, indent=2, ensure_ascii=False)

        # Also save to current debug files for backwards compatibility
        with open("debug/debug_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        with open("debug/debug_response.json", "w", encoding="utf-8") as f:
            json.dump(response_data, f, indent=2, ensure_ascii=False)

        log(f"Debug data saved to {debug_file} ({request_type} request)")
    except Exception as e:
        log(f"Error saving debug data: {e}")

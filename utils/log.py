import os
import json

def log(message):
    """Log a message, respecting DEBUG setting."""
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    if debug:
        # print with purple color
        print("\033[94m" + str(message) + "\033[0m")
    else:
        # Only print messages that are essential for user feedback
        if isinstance(message, str) and any(keyword in message for keyword in [
            "Error",
            "Please",
            "Warning",
            "Success",
            "✅",
            "❌",
        ]):
            print(str(message))

def save_debug(data, response):
    """Save the debug data and response to files."""
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    if not debug:
        return

    try:
        # Create debug directory if it doesn't exist
        os.makedirs('debug', exist_ok=True)
        
        # Save data
        with open("debug/debug_data.json", "w", encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Convert response to JSON-serializable format
        response_data = None
        if hasattr(response, 'json'):
            try:
                response_data = response.json()
            except:
                response_data = {'text': response.text}
        else:
            response_data = response

        # Save response
        with open("debug/debug_response.json", "w", encoding='utf-8') as f:
            json.dump(response_data, f, indent=2, ensure_ascii=False)
            
        log("Debug data saved to debug/debug_data.json and debug/debug_response.json")
    except Exception as e:
        log(f"Error saving debug data: {e}")

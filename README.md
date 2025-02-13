# Mini-AutoGPT

Mini-AutoGPT is a demonstration of a fully autonomous AI using local LLMs. It is built with Python 3.11 and uses `python-telegram-bot` for communication. This project serves as a guide for readers of my book "Unlocking the Power of Auto-GPT and Its Plugins" and as a preview of Sophie-AI, a more advanced autonomous AI. It defaults to Llama 3.1 8B and LM Studio.

### Important Note

This project uses the `python-telegram-bot` library for Telegram communication. Please ensure you install the correct package using `python-telegram-bot`. Installing the `telegram` package will not work and is not supported.

## Table of Contents 📚

- [What's Cooking? 🍳](#whats-cooking-)
- [Setup](#setup)
- [Usage](#usage)
- [Experimental Notice](#experimental-notice)
- [Contributing](#contributing)
- [Mini-AutoGPT in Action](#mini-autogpt-in-action)
- [License](#license)

## What's Cooking?

Mini-AutoGPT is a lightweight AI bot designed to run locally and interact with you via Telegram. It's simple to use and modify, capable of handling complex chat applications, and allows local AI experimentation without cloud services.

Key components:

- **Python 3.11**: Core language
- **python-telegram-bot**: Telegram communication
- **Autonomy**: No manual intervention

## Setup

To get started:

1. Python 3.11 or later installed on your machine.
2. A Telegram bot token (get yours from [@BotFather](https://t.me/BotFather)).
3. Clone this repository:
    ```bash
    git clone https://github.com/yourusername/mini-autogpt.git
    cd mini-autogpt
    ```
4. Run the setup script:
    ```bash
    ./setup.sh
    ```
   This will:
   - Create a Python virtual environment
   - Install all dependencies
   - Create a .env file from template
5. Run a local LLM server:
    - LMStudio
    - oobabooga/textgeneration-webui
    - Ollama
6. Update `.env` with the API URL and server type. Examples:

    - **LMStudio:**
        ```
        API_URL="http://localhost:1234/v1/"
        LLM_SERVER_TYPE="lmstudio"
        ```
    - **Ollama:**
        ```
        API_URL="http://localhost:11434/api/generate"
        LLM_SERVER_TYPE="ollama"
        ```
    - **oobabooga/textgeneration-webui:**
        ```
        API_URL="[The API URL provided by the web UI]"
        LLM_SERVER_TYPE="oobabooga"
        ```

## LLM Models known to work with Mini-AutoGPT
- Meta/LLama-3-8B-Instruct
- NousResearch/Hermes-2-Pro-Mistral-7B
- argilla/CapybaraHermes-2.5-Mistral-7B
- Intel/neural-chat-7b-v3-1
- Nexusflow/Starling-LM-7B-beta
- mistralai/Mixtral-8x7B-Instruct-v0.1

## Usage 🔧

After setup, run the script:

```bash
./run.sh
```

## Experimental Notice 🧪

Mini-AutoGPT is still experimental software. It may exhibit unexpected behavior. Please use with caution.

## Contributing 🤝

Feel free to fork, star, and submit pull requests.
Bugs can be reported in the issues section. Contributions are welcome!

Mini-AutoGPT in Action 🎬

Here's a snippet of what to expect when you fire up Mini-AutoGPT:

```python
                           
                                                 
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
              

Hello my friend!
I am Mini-Autogpt, a small version of Autogpt for smaller llms.
I am here to help you and will try to contact you as soon as possible!

Note: I am still in development, so please be patient with me! <3

Forgetting everything...
My memory is empty now, I am ready to learn new things! 

*** I am thinking... ***
```

Mini-AutoGPT is the small bot with a big dream: to make LLMs accessible on your local machine. Join us in nurturing this tiny digital marvel!

Mini-AutoGPT: Small in size, big on personality. 🌟

## License 📜

This project is licensed under the MIT License.

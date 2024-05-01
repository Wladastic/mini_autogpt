# Mini-AutoGPT 🤖🚀

Welcome to the home of Mini-AutoGPT, the pocket-sized AI with the heart of a giant. Here to demonstrate that local LLMs can still rock your digital world, Mini-AutoGPT runs on pure Python 3.11 and communicates through the magic of `python-telegram-bot`. It's experimental, autonomous, and always ready to chat—what more could you ask for in a desktop companion?

This Repository is mainly a demonstration for using local LLMs for fully autonomous AI.
It is meant as a guide for readers of my Book "Unlocking the Power of Auto-GPT and Its Plugins"

This Repository is also a Preview of Sophie-AI, a fully autonomous AI that runs on your local machine and can be used for various tasks, which acomplishes more complex thoughts and tasks than Mini-AutoGPT.

## Table of Contents 📚

- [What's Cooking? 🍳](#whats-cooking-)
- [Setup](#setup)
- [Usage](#usage)
- [Experimental Notice](#experimental-notice)
- [Contributing](#contributing)
- [Mini-AutoGPT in Action](#mini-autogpt-in-action)
- [License](#license)

## What's Cooking?

Mini-AutoGPT isn't just a stripped-down version of some monolithic AI—it's your friendly neighborhood bot that lives right in your Telegram! It’s designed to be simple enough for anyone to tinker with, yet robust enough to handle the sophisticated needs of modern chat applications.

Due to the nature of local LLMs (3B, 4B, 7B, 8B etc.) being smaller than their cloud counterparts, Mini-AutoGPT is a great way to experiment with AI on your local machine without having to pay for cloud services.


Here's a sneak peek of its main ingredients:

- **Python 3.11**: Fresh and powerful.
- **python-telegram-bot**: Connects you directly to your users via Telegram.
- **Autonomy**: Runs fully on its own, no hand-holding required.

## Setup

To get started, you'll need:

1. Python 3.11 installed on your machine.
2. A Telegram bot token (get yours from [@BotFather](https://t.me/BotFather)).
3. Clone this repository and install dependencies:

    ```bash
    git clone https://github.com/yourusername/mini-autogpt.git
    cd mini-autogpt
    pip install -r requirements.txt
4. Update the .env file with your Telegram bot token.

## Usage 🔧

Just run the script, and your bot will come to life:

```bash
./run.sh
```

or

```bash
python3.11 main.py
```

## Experimental Notice 🧪

Mini-AutoGPT is still experimental. It might get a little too excited and repeat what you say or surprise you with unexpected wisdom. Handle it with care and affection!

## Contributing 🤝

Feel free to fork, star, and submit pull requests.
Bugs can be reported in the issues section. Help Mini-AutoGPT learn the ways of this vast digital universe!

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

This project is licensed under the MIT License. For more information, please refer to the [LICENSE](LICENSE) file.

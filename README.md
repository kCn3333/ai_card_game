# ♠ AI Card Game

A desktop Blackjack game where you play against a local AI opponent powered by Ollama/LLM models.

![Python](https://img.shields.io/badge/Python-3.13-blue)
![PySide6](https://img.shields.io/badge/GUI-PySide6-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- 🎰 **Casino-style UI** - Beautiful green felt table with overlapping cards
- 🤖 **AI Opponent** - Plays against you using local LLM (Ollama)
- 💬 **Trash Talk** - Aggressive AI that comments on the game
- 📊 **Game Console** - Timestamped logs of all game events
- ⚙️ **Configurable** - Change AI host/model in Settings
- 🎨 **SVG Cards** - Crisp vector graphics at any size

## Screenshots

*Coming soon*

## Requirements

- Python 3.13+
- [Ollama](https://ollama.ai/) running locally (or compatible LLM server)
- A model like `gemma3:4b`, `llama3`, `qwen2.5`, etc.

## Installation

1. Clone the repository:
```bash
git clone https://github.com/kCn3333/ai_card_game.git
cd ai_card_game
```

2. Create a virtual environment (Python 3.13):
```bash
py -3.13 -m venv .venv
.\.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Make sure Ollama is running with a model:
```bash
ollama run gemma3:4b
```

## Usage

Run the game:
```bash
python -m ai_card_game.app.main
```

### Controls

- **HIT** - Draw another card
- **STAND** - End your turn, let AI play
- **NEW GAME** - Start a fresh game

### Settings

Go to **Settings → AI Settings...** to:
- Change the AI host (default: `http://127.0.0.1:11434`)
- Change the model (default: `gemma3:4b`)
- Test the connection

## Project Structure

```
ai_card_game/
├── app/
│   ├── ai/                 # AI client and Blackjack agent
│   ├── assets/
│   │   ├── cards/          # 52 card SVGs
│   │   ├── backs/          # Card back designs
│   │   └── icons/          # App icons
│   ├── config/             # Settings and defaults
│   ├── core/
│   │   ├── cards.py        # Card and Deck classes
│   │   └── blackjack/      # Blackjack game engine
│   ├── db/                 # SQLite database
│   └── ui/                 # PySide6 UI components
├── requirements.txt
└── README.md
```

## Roadmap

- [ ] Statistics tracking (wins/losses)
- [ ] Persist settings to SQLite
- [ ] Multiple card back designs
- [ ] Sound effects
- [ ] More card games (Poker, War, etc.)
- [ ] Betting system

## License

MIT License - feel free to use and modify!

## Author

Made with ♠ by kCn

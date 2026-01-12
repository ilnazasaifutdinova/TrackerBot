# Tracker Discord Bot
### A simple Discord bot that monitors external web pages for content updates and sends notifications to a specified Discord channel.

## Features
- Periodic monitoring of external web resources
- Discord embed notifications when new content appears
- Configurable via environment variables
- Low-frequency requests with fallback parsing logic

## Tech Stack
- Python 3.12
- requests
- BeautifulSoup
- discord.py

## Installation
```bash
git clone https://github.com/ilnazasaifutdinova/TrackerBot.git
cd TrackerBot
pip install -r requirements.txt
```

## Configuration
```env
DISCORD_TOKEN=ваш_токен_бота
CHANNEL_ID=id_канала_для_уведомлений
MANGA_URL=https://ваша-манга
```

## Run
```bash
python3 bot.py
```

## License
MIT License

## Disclaimer 
This project is for educational purposes only. It performs low-frequency requests and does not bypass any website protections.

# LinkedIn AI News Bot

An automated bot that posts curated AI/ML news content to LinkedIn using LLM-powered content generation.

## Features

- 🤖 Automated AI news curation and posting to LinkedIn
- 🎯 Smart content filtering and relevance scoring
- ✍️ LLM-powered content generation with multiple posting styles
- 📊 Analytics tracking and reporting
- 🔔 Discord notifications for important events
- 💬 Automated comment monitoring and response generation
- ⏰ Configurable posting schedule and frequency

## Requirements

- Python 3.8+
- LinkedIn API credentials (Client ID and Secret)
- LLM API key (supports Groq by default)
- Discord webhook URL (optional, for notifications)
- NewsAPI key (optional, for additional news sources)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/linkedin_ai_news_bot.git
cd linkedin_ai_news_bot
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root with your credentials:

```
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LLM_API_KEY=your_llm_api_key
LLM_PROVIDER=groq
DISCORD_WEBHOOK_URL=your_discord_webhook_url  # Optional
NEWSAPI_KEY=your_newsapi_key  # Optional
```

## Configuration

The bot's behavior can be customized through the `config.py` file:

- News sources (RSS feeds and APIs)
- Posting frequency and timing
- Content generation styles
- Quality thresholds
- And more

## Usage

The bot can be run in different modes:

1. Single post mode (for testing):

```bash
python main.py --once
```

2. Continuous mode with scheduler:

```bash
python main.py --days 30 --update-interval 30
```

3. View analytics:

```bash
python main.py --analytics
```

### Command Line Arguments

- `--once`: Run a single post cycle
- `--analytics`: Display posting analytics
- `--days`: Number of days to run the scheduler (default: 30)
- `--update-interval`: Update interval in minutes (default: 30)

## Features in Detail

### News Curation

- Fetches news from multiple sources including RSS feeds and NewsAPI
- Filters articles based on relevance and recency
- Prevents duplicate posts using history tracking

### Content Generation

- Uses LLM to generate engaging LinkedIn posts
- Supports multiple posting styles:
  - Thought Leader
  - Industry Expert
  - Curious Professional
  - Data-Driven
- Weekend post variations
- Quality evaluation before posting

### Monitoring & Analytics

- Tracks post performance
- Monitors and responds to comments
- Discord notifications for important events
- Detailed analytics reporting

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Your chosen license]

## Disclaimer

This bot is for educational and research purposes. Make sure to comply with LinkedIn's terms of service and API usage guidelines when using this bot.

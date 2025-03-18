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

## Architecture

### Components

- `src/news_fetcher.py`: News aggregation and filtering logic
- `src/content_generator.py`: LLM-powered content generation
- `src/linkedin_api.py`: LinkedIn API integration
- `src/analytics.py`: Performance tracking and reporting
- `src/scheduler.py`: Scheduling and timing management
- `src/monitor.py`: Comment monitoring and response system

### Data Flow

1. News Collection → Filtering → Content Generation → Post Creation → Analytics
2. Parallel processes for comment monitoring and engagement
3. Asynchronous analytics processing and reporting

## Deployment

### Local Development

1. Set up pre-commit hooks:

```bash
pre-commit install
```

2. Run tests:

```bash
pytest tests/
```

### Production Deployment

1. Using Docker:

```bash
docker build -t linkedin-ai-bot .
docker run -d --env-file .env linkedin-ai-bot
```

2. Using PM2 (Node.js process manager):

```bash
pm2 start main.py --name "linkedin-bot" --interpreter python3
```

3. Using systemd service:
   Create `/etc/systemd/system/linkedin-bot.service`:

```ini
[Unit]
Description=LinkedIn AI News Bot
After=network.target

[Service]
User=youruser
WorkingDirectory=/path/to/linkedin_ai_news_bot
Environment=PYTHONPATH=/path/to/linkedin_ai_news_bot
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Advanced Configuration

### Content Generation Settings

```python
# config.py
CONTENT_SETTINGS = {
    'max_tokens': 500,
    'temperature': 0.7,
    'posting_styles': {
        'thought_leader': {
            'tone': 'authoritative',
            'structure': 'insight + analysis + call-to-action'
        },
        # ... other styles
    }
}
```

### Rate Limiting

- LinkedIn API: 100 requests/day per user
- Content Generation: Configurable based on API provider
- News Fetching: Adjustable intervals (default: 30 minutes)

## Troubleshooting

### Common Issues

1. API Rate Limits

   - Symptom: 429 Too Many Requests
   - Solution: Adjust request timing in `config.py`

2. Content Generation Failures

   - Symptom: Empty or invalid content
   - Solution: Check LLM API key and adjust parameters

3. Scheduling Issues
   - Symptom: Missed posts
   - Solution: Verify timezone settings and cron configurations

### Logging

Logs are stored in `logs/` directory:

- `app.log`: General application logs
- `api.log`: API interaction logs
- `error.log`: Error tracking

## Best Practices

1. Content Guidelines

   - Maintain professional tone
   - Avoid controversial topics
   - Include relevant hashtags
   - Credit sources appropriately

2. Engagement Strategy

   - Response timing: Within 2-4 hours
   - Engagement ratio: 1:3 (responses:reactions)
   - Comment quality threshold: 0.7

3. Performance Optimization
   - Cache frequently accessed data
   - Implement exponential backoff
   - Regular database cleanup

## Monitoring

### Health Checks

- Endpoint: `/health`
- Metrics: CPU, memory, API status
- Alerting: Discord + Email

### Performance Metrics

- Post engagement rates
- API response times
- Content quality scores
- System resource usage

## Roadmap

- [ ] Multi-language support
- [ ] AI-powered image generation
- [ ] Advanced analytics dashboard
- [ ] A/B testing framework
- [ ] Community management features

## Support

For support, please:

1. Check the [FAQ](docs/FAQ.md)
2. Search [existing issues](https://github.com/yourusername/linkedin_ai_news_bot/issues)
3. Create a new issue with:
   - System details
   - Error logs
   - Steps to reproduce

# Social Content Kit

An educational Telegram bot with exactly three persistent menu buttons:

- **Post Ideas**: five topic-based practice prompts.
- **Caption Builder**: a caption template with Friendly, Professional or Casual tone.
- **Content Planner**: a seven-day content practice plan.

All results are delivered in Telegram. This is a deterministic template tool, not an AI writer. It does not connect to social accounts, post on users' behalf, sell engagement, or direct users to websites. No database or third-party API key is required.

## Run

Use Python 3.12 or newer. The bot uses only the Python standard library.

1. Create your bot with BotFather and set its profile picture to your logo.
2. Add the bot token as the secret environment variable `BOT_TOKEN`. Never commit the token.
3. Start with `python bot.py`.

`bot.py` defines the name, About (`ABOUT`) and Description (`DESCRIPTION`) and applies them at startup in the default language and English. It also registers `/start`, `/help`, `/cancel` and `/privacy`.

Deploy as a **background worker** with start command `python bot.py`; no web port is needed. Run only one instance per token to avoid Telegram polling conflicts. This repository does not deploy automatically by itself.

## Privacy and behavior

Pending input is held in memory for up to 30 minutes, cleared on completion or `/cancel`, and lost on restart. The bot stores at most 2,000 pending sessions. Expired sessions are removed when messages arrive. No message content or tokens are logged. Telegram receives messages through its Bot API. There are no external website buttons or redirect modes. Input links and usernames are rejected to keep outputs as plain educational topics.

Run `python -m unittest -v` for offline checks. A real token is required to verify Telegram delivery and profile setup.

## Advertising

Describe the actual educational tools in the ad. Keep the profile complete, use the generated logo, and test all three flows on mobile and desktop before advertising. The bot does not guarantee marketing outcomes or ad approval. Telegram makes the final moderation decision.

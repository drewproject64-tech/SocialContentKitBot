"""Educational social content templates. Only connects to the Telegram Bot API."""
import json
import logging
import os
import re
import signal
import time
from collections import OrderedDict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

NAME = "Social Content Kit"
ABOUT = "Educational social media tools: post ideas, caption templates and a 7-day content planner."
DESCRIPTION = (
    "Learn to plan social media content with Social Content Kit.\n\n"
    "Post Ideas: get five prompts for your niche.\n"
    "Caption Builder: turn a topic into a caption template.\n"
    "Content Planner: create a seven-day practice plan.\n\n"
    "All tools work inside Telegram. Educational templates only; no account access or automatic posting."
)
BUTTONS = ("Post Ideas", "Caption Builder", "Content Planner")
MENU = {"keyboard": [[{"text": label}] for label in BUTTONS], "resize_keyboard": True, "is_persistent": True}
WELCOME = (
    "Welcome to Social Content Kit!\n\n"
    "Practice creating social media content with simple, topic-based templates. "
    "Choose Post Ideas, Caption Builder or Content Planner below.\n\n"
    "Everything stays inside Telegram. No social account login is needed. "
    "Use /help for guidance or /cancel to return to the menu."
)
running = True


class TelegramError(Exception):
    def __init__(self, code, retry_after=0):
        self.code, self.retry_after = code, retry_after
        super().__init__(f"Telegram API error {code}")


class API:
    def __init__(self, token):
        self.base = "https://api.telegram.org/bot" + token + "/"

    def call(self, method, **data):
        request = Request(self.base + method, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=40) as response:
                result = json.load(response)
        except HTTPError as error:
            try:
                result = json.load(error)
            except (ValueError, OSError):
                raise TelegramError(error.code) from None
        if not result.get("ok"):
            raise TelegramError(result.get("error_code", 0), result.get("parameters", {}).get("retry_after", 0))
        return result["result"]


def clean_topic(text):
    topic = " ".join(text.split())
    if not 2 <= len(topic) <= 160:
        raise ValueError("Please enter a topic between 2 and 160 characters.")
    if re.search(r"https?://|www\.|t\.me/|@\w+|\b\w+[.]\w{2,}(?:/|\b)", topic, re.I):
        raise ValueError("Please describe your topic in words, without links or usernames.")
    return topic


def post_ideas(topic):
    prompts = [
        f"Explain one beginner concept about {topic} in three clear steps.",
        f"Show a behind-the-scenes example of how you work on {topic}.",
        f"Answer a common beginner question about {topic} with an example.",
        f"Share a practical checklist for getting started with {topic}.",
        f"Ask your audience which part of {topic} they want to learn next.",
    ]
    return "Five post ideas\n\n" + "\n\n".join(f"{i}. {p}" for i, p in enumerate(prompts, 1)) + "\n\nPractice tip: choose one idea and add an original example."


def caption(topic, tone):
    openings = {"friendly": f"Let's talk about {topic}.", "professional": f"A practical look at {topic}.", "casual": f"Today's topic: {topic}."}
    return (
        f"Caption template ({tone})\n\n{openings[tone]}\n\n"
        "Start with one clear idea, explain it with a simple example, and give your audience "
        "one useful step to try.\n\n"
        f"What would you like to learn about {topic}?\n\n"
        "Before posting: replace the middle paragraph with your specific tip and example."
    )


def planner(topic):
    days = [
        ("Introduce", "Explain what you cover and who it helps."),
        ("Teach", "Share one beginner tip with a concrete example."),
        ("Demonstrate", "Show your process with a photo or short video."),
        ("Answer", "Address one common question with a clear explanation."),
        ("Compare", "Explain two approaches and when each can help."),
        ("Discuss", "Ask an open question and respond thoughtfully to replies."),
        ("Review", "Recap the week's lessons and choose next week's topic."),
    ]
    return f"Seven-day practice plan: {topic}\n\n" + "\n\n".join(f"Day {i} — {title}\n{task}" for i, (title, task) in enumerate(days, 1)) + "\n\nAdapt this schedule to your audience. Review clarity and accuracy before posting."


class Bot:
    def __init__(self, api):
        self.api = api
        self.states = OrderedDict()

    def send(self, chat, text):
        self.api.call("sendMessage", chat_id=chat, text=text, reply_markup=MENU, link_preview_options={"is_disabled": True})

    def remember(self, key, step, topic=None):
        self.states[key] = (step, topic, time.monotonic())
        self.states.move_to_end(key)
        while len(self.states) > 2000:
            self.states.popitem(last=False)

    def handle(self, message):
        chat = message["chat"]["id"]
        if message["chat"].get("type") != "private":
            return
        key = (chat, message.get("from", {}).get("id", chat))
        now = time.monotonic()
        while self.states and now - next(iter(self.states.values()))[2] > 1800:
            self.states.popitem(last=False)
        text = message.get("text", "").strip()
        command = text.split(maxsplit=1)[0].split("@")[0].lower() if text else ""
        if command in ("/start", "/help", "/cancel", "/privacy"):
            self.states.pop(key, None)
            if command == "/privacy":
                self.send(chat, "This bot keeps your current input temporarily in memory for up to 30 minutes. No social account credentials are requested. Inputs are not saved to a database or sent to an AI service. Telegram processes messages under its own policies. Use /cancel to clear your current input.")
            else:
                self.send(chat, WELCOME if command == "/start" else "Choose a tool, then enter a niche or topic (2–160 characters). Caption Builder also asks for Friendly, Professional or Casual. Outputs are educational templates to adapt before publishing. /cancel clears your current input. /privacy explains data handling.")
            return
        if text in BUTTONS:
            self.remember(key, text)
            self.send(chat, {"Post Ideas": "What niche would you like post ideas for? Example: handmade clothing.", "Caption Builder": "What is your post about? Example: beginner tips for taking product photos.", "Content Planner": "What niche or business type is your plan for? Example: a local bakery."}[text])
            return
        state = self.states.get(key)
        if not state:
            self.send(chat, "Choose one of the three tools below to get started.")
            return
        step, topic, _ = state
        if step == "tone":
            tone = text.lower()
            if tone not in ("friendly", "professional", "casual"):
                self.send(chat, "Type Friendly, Professional or Casual. You can also choose another tool below.")
                return
            result = caption(topic, tone)
        else:
            try:
                topic = clean_topic(text)
            except ValueError as error:
                self.send(chat, str(error))
                return
            if step == "Caption Builder":
                self.remember(key, "tone", topic)
                self.send(chat, "Choose your caption tone by typing Friendly, Professional or Casual.")
                return
            result = post_ideas(topic) if step == "Post Ideas" else planner(topic)
        self.states.pop(key, None)
        self.send(chat, result)


def stop(*_):
    global running
    running = False


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    token = os.environ.get("BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("Set BOT_TOKEN before starting the bot.")
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    api = API(token)
    # Default and English metadata are managed here, rather than only in BotFather.
    for language in ("", "en"):
        api.call("setMyName", name=NAME, language_code=language)
        api.call("setMyShortDescription", short_description=ABOUT, language_code=language)
        api.call("setMyDescription", description=DESCRIPTION, language_code=language)
    api.call("setMyCommands", commands=[{"command": name, "description": description} for name, description in [("start", "Open the three content tools"), ("help", "How to use the educational tools"), ("cancel", "Clear input and return to the menu"), ("privacy", "How your input is handled")]])
    api.call("deleteWebhook", drop_pending_updates=False)
    bot, offset = Bot(api), 0
    logging.info("Social Content Kit started")
    while running:
        try:
            updates = api.call("getUpdates", offset=offset, timeout=25, allowed_updates=["message"])
            for update in updates:
                try:
                    if "message" in update:
                        bot.handle(update["message"])
                except (TelegramError, URLError, TimeoutError, OSError):
                    logging.warning("Could not deliver a response; user can retry the tool.")
                offset = update["update_id"] + 1
        except TelegramError as error:
            if error.code in (401, 409):
                raise SystemExit("Invalid bot token or another polling instance is running.") from None
            logging.warning("Telegram temporarily unavailable (%s)", error.code)
            time.sleep(max(3, min(error.retry_after, 60)))
        except (URLError, TimeoutError, OSError):
            logging.warning("Connection interrupted; retrying")
            time.sleep(3)


if __name__ == "__main__":
    main()

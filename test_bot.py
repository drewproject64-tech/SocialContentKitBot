import unittest
from bot import Bot, ABOUT, DESCRIPTION, clean_topic


class FakeAPI:
    def __init__(self):
        self.messages = []

    def call(self, method, **data):
        self.messages.append(data)


class BotTests(unittest.TestCase):
    def setUp(self):
        self.api = FakeAPI()
        self.bot = Bot(self.api)

    def send(self, text, user=1):
        self.bot.handle({"chat": {"id": user, "type": "private"}, "from": {"id": user}, "text": text})
        return self.api.messages[-1]["text"]

    def test_tools(self):
        self.send("Post Ideas")
        self.assertIn("5. Ask", self.send("baking"))
        self.send("Content Planner")
        self.assertIn("Day 7", self.send("photography"))
        self.send("Caption Builder")
        self.assertIn("tone", self.send("handmade bags"))
        self.assertIn("Type Friendly", self.send("unknown"))
        result = self.send("Professional")
        self.assertIn("handmade bags", result)
        self.assertIn("professional", result)

    def test_cancel_and_user_isolation(self):
        self.send("Post Ideas")
        self.assertIn("Choose one", self.send("baking", user=2))
        self.send("/cancel")
        self.assertFalse(self.bot.states)

    def test_invalid_input_and_metadata(self):
        for value in ("x", "a" * 161, "https://example.com", "@example"):
            with self.assertRaises(ValueError):
                clean_topic(value)
        self.assertLessEqual(len(ABOUT), 120)
        self.assertLessEqual(len(DESCRIPTION), 512)
        self.send("Post Ideas")
        self.assertIn("without links", self.send("www.example.com"))
        self.assertIn("baking", self.send("baking"))


if __name__ == "__main__":
    unittest.main()

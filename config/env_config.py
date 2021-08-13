from rewards.aws.helpers import get_secret
import os


class EnvConfig:
    def __init__(self):
        self.graph_api_key = get_secret("boost-bot/graph-api-key-d", "GRAPH_API_KEY")
        self.test_webhook_url = get_secret(
            "boost-bot/test-discord-url", "TEST_WEBHOOK_URL"
        )
        self.discord_webhook_url = get_secret("DISCORD_WEBHOOK_URL", "")
        self.test = os.getenv("TEST", "False").lower() in ["true", "1", "t", "y", "yes"]
        self.bucket = (
            "badger-staging-merkle-proofs" if self.test else "badger-merkle-proofs"
        )

    def get_webhook_url(self):
        if self.test:
            return self.test_webhook_url
        else:
            return self.discord_webhook_url


env_config = EnvConfig()

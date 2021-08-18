from rewards.aws.helpers import get_secret

import os
import dotenv
from web3 import Web3

dotenv.load_dotenv()


class EnvConfig:
    def __init__(self):
        self.test = os.getenv("TEST", "False").lower() in ["true", "1", "t", "y", "yes"]
        self.local = os.getenv("LOCAL", "False").lower() in [
            "true",
            "1",
            "t",
            "y",
            "yes",
        ]
        self.graph_api_key = (
            get_secret("boost-bot/graph-api-key-d", "GRAPH_API_KEY")
            if not self.local
            else os.getenv("graph_api_key", "")
        )
        self.test_webhook_url = (
            get_secret("boost-bot/test-discord-url", "TEST_WEBHOOK_URL")
            if not self.local
            else os.getenv("test_webhook_url", "")
        )
        self.discord_webhook_url = (
            get_secret("boost-bot/prod-disc ord-url", "DISCORD_WEBHOOK_URL")
            if not self.local
            else os.getenv("discord_webhook_url", "")
        )
        self.web3 = Web3(
            Web3.HTTPProvider(
                get_secret("quiknode/eth-node-url", "NODE_URL")
                if not self.local
                else os.getenv("rpc", "")
            )
        )
        self.aws_access_key_id = (
            "" if not self.local else os.getenv("aws_access_key_id", "")
        )
        self.aws_secret_access_key = (
            "" if not self.local else os.getenv("aws_secret_access_key", "")
        )

    def get_webhook_url(self):
        if self.test:
            return self.test_webhook_url
        else:
            return self.discord_webhook_url


env_config = EnvConfig()

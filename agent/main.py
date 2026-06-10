from __future__ import annotations

import argparse
import asyncio

from agent.config import AgentConfig
from agent.server import Agent
from shared.utils.logging import setup_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PC Remote Admin agent")
    parser.add_argument("--config", default="infra/configs/agent.example.yaml")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_logging()
    config = AgentConfig.from_file(args.config)
    asyncio.run(Agent(config).start())


if __name__ == "__main__":
    main()

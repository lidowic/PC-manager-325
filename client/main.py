from __future__ import annotations

import argparse
import sys

from client.app import run_app
from client.config import ClientConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PC Remote Admin client")
    parser.add_argument("--config", default="infra/configs/client.example.yaml")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = ClientConfig.from_file(args.config)
    sys.exit(run_app(config))


if __name__ == "__main__":
    main()

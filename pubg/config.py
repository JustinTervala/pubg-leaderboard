import os
import logging
import sys

from dotenv import dotenv_values


logger = logging.getLogger(__name__)


def load_config() -> dict[str, str]:
    config = dotenv_values(".env")
    secret_config = dotenv_values("/etc/secrets/.env.secret") | dotenv_values(
        ".env.secret"
    )
    merged_config = config | secret_config
    printed_configs = [
        f"{key}={value}" for key, value in config.items() if key not in secret_config
    ] + [f"{key}=******" for key in secret_config]
    logger.info(f"Using config from file {', '.join(printed_configs)}")
    return merged_config | os.environ


def configure_logging(debug: bool=False) -> None:
    level = logging.DEBUG if debug else logging.INFO
    root = logging.getLogger()
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)

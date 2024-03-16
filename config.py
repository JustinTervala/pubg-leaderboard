from dotenv import dotenv_values
import os


def load_config() -> dict[str, str]:
    config = dotenv_values(".env")
    secret_config = dotenv_values("/etc/secrets/.env.secret") | dotenv_values(
        ".env.secret"
    )
    merged_config = config | secret_config
    printed_configs = [
        f"{key}={value}" for key, value in config.items() if key not in secret_config
    ] + [f"{key}=******" for key in secret_config]
    print(f"Using config from file {', '.join(printed_configs)}")
    return merged_config | os.environ

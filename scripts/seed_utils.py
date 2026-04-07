import os
from typing import Iterable

from faker import Faker

fake = Faker()


def set_db_env(prefix: str, user: str, password: str, host: str, port: str, database: str) -> None:
    os.environ.setdefault(f"{prefix}_USERNAME", user)
    os.environ.setdefault(f"{prefix}_PASSWORD", password)
    os.environ.setdefault(f"{prefix}_HOST", host)
    os.environ.setdefault(f"{prefix}_PORT", port)
    os.environ.setdefault(f"{prefix}_DATABASE", database)


def random_image_url(seed: str) -> str:
    return f"https://picsum.photos/seed/{seed}/640/480"


def choose_tags(words: Iterable[str]) -> str:
    return ",".join(sorted(set(words)))

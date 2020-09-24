import string
import time
import uuid
from random import randint, choice, random


def generate_random_input_message() -> dict:
    return {
        "uid": str(uuid.uuid4()),
        "text": generate_random_text()
    }


def generate_random_text() -> str:
    length = randint(1, 20)
    letters = string.ascii_lowercase
    text = ''.join(choice(letters) for _ in range(length))
    return text


def generate_random_output_message(input_message: dict, publish_ts=None) -> dict:
    output_message = {
        "uid": input_message["uid"],
        "text": input_message["text"],
        "category": str(randint(1, 10)),
        "subcategory": str(randint(1, 100)),
        "confidence": random(),
        "model": "model x",
        "version": randint(1, 100),
        "streaming_consume_ts": int(time.time()*1000)
    }
    if publish_ts is not None:
        output_message["publish_ts"] = int(publish_ts)
    return output_message


def generate_random_output_data(input_data: dict) -> dict:
    output_data = {
        "uid": input_data["uid"],
        "text": input_data["text"],
        "category": str(randint(1, 10)),
        "subcategory": str(randint(1, 100)),
        "confidence": random(),
        "model": "model x",
        "version": randint(1, 100),
    }
    return output_data

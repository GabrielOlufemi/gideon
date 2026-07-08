import json
import httpx
from exceptions import AuthError, NetworkError, NoCreditsError

import os
from dotenv import load_dotenv


OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")

CONNECT_LIMIT = 10.0
WRITE_LIMIT = 10.0
READ_LIMIT = 300.0
POOL_LIMIT = 10.0

TIMEOUT = httpx.Timeout(connect=CONNECT_LIMIT, read=READ_LIMIT, write=WRITE_LIMIT, pool=POOL_LIMIT)

def chat(messages: list[dict], model: str, tools: list[dict] = None) -> dict:

    body = {
        "model" : model,
        "messages" : messages
    }

    if tools:
        body["tools"] = tools


    try:

        response = httpx.post(
            url = "https://openrouter.ai/api/v1/chat/completions",

            headers = {
                "Authorization" : f"Bearer {OPENROUTER_KEY}",
            },

            data=json.dumps(body),
            timeout=TIMEOUT
        )

        if response.status_code == 401:
            raise AuthError("API key rejected")

        if response.status_code == 402:
            raise NoCreditsError("Insufficient credits")

        return json.loads(response.text)
    except httpx.TimeoutException:
        raise NetworkError("Request to Openrouter timed out. Try again in a moment")
    
    except httpx.ConnectError:
        raise NetworkError("Could not reach OpenRouter")


def validate_key(api_key: str) -> bool:

    try:

        response = httpx.get(
            url = "https://openrouter.ai/api/v1/key",
            headers = {
                "Authorization" : f"Bearer {api_key}"
            },
            timeout=TIMEOUT
        )

        if response.status_code == 401:
            raise AuthError("API key rejected")
        
        if response.status_code == 402:
            raise NoCreditsError("Insufficient credits")
        
        data = response.json()["data"]

        if data["limit_remaining"] is None or data["limit_remaining"] > 0: 
            return True
        else:
            return False
    except httpx.TimeoutException:
        raise NetworkError("Request to Openrouter timed out. Try again in a moment")

    except httpx.ConnectError:
        raise NetworkError("Could not reach Openrouter")
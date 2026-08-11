import json
import httpx
from exceptions import AuthError, NetworkError, NoCreditsError

CONNECT_LIMIT = 10.0
WRITE_LIMIT = 10.0
READ_LIMIT = 300.0
POOL_LIMIT = 10.0

TIMEOUT = httpx.Timeout(connect=CONNECT_LIMIT, read=READ_LIMIT, write=WRITE_LIMIT, pool=POOL_LIMIT)

# currently redundant
def chat(messages: list[dict], model: str, api_key: str, tools: list[dict] = None) -> dict:

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
                "Authorization" : f"Bearer {api_key}",
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


def chat_stream(messages: list[dict], model: str, api_key: str, tools: list[dict] = None):
    """Stream a chat completion. Yields content tokens as strings, then yields the final message dict."""

    body = {
        "model": model,
        "messages": messages,
        "stream": True
    }

    if tools:
        body["tools"] = tools

    with httpx.Client(timeout=TIMEOUT) as client:
        try:
            with client.stream(
                "POST",
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                },
                data=json.dumps(body),
            ) as response:

                if response.status_code == 401:
                    raise AuthError("API key rejected")
                if response.status_code == 402:
                    raise NoCreditsError("Insufficient credits")

                content_so_far = ""
                tool_calls_by_index = {}
                usage = None

                for line in response.iter_lines():
                    if not line.startswith("data: "):
                        continue

                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    choice = chunk["choices"][0]
                    delta = choice.get("delta", {})
                    finish_reason = choice.get("finish_reason")

                    # Capture usage from the chunk if present (OpenRouter includes it
                    # in the final streaming chunk alongside finish_reason)
                    if "usage" in chunk:
                        usage = chunk["usage"]

                    # Content tokens
                    content = delta.get("content")
                    if content:
                        content_so_far += content
                        yield content

                    # Tool call deltas — accumulate by index
                    tool_calls = delta.get("tool_calls")
                    if tool_calls:
                        for tc in tool_calls:
                            idx = tc["index"]
                            if idx not in tool_calls_by_index:
                                tool_calls_by_index[idx] = {
                                    "id": tc.get("id", ""),
                                    "type": tc.get("type", "function"),
                                    "function": {"name": "", "arguments": ""}
                                }
                            acc = tool_calls_by_index[idx]
                            if tc.get("id"):
                                acc["id"] = tc["id"]
                            if tc.get("type"):
                                acc["type"] = tc["type"]
                            if "function" in tc:
                                if tc["function"].get("name"):
                                    acc["function"]["name"] += tc["function"]["name"]
                                if tc["function"].get("arguments"):
                                    acc["function"]["arguments"] += tc["function"]["arguments"]

                    # Stream finished — yield the complete message
                    if finish_reason:
                        message = {
                            "role": "assistant",
                            "content": content_so_far or None
                        }
                        if tool_calls_by_index:
                            message["tool_calls"] = [
                                tool_calls_by_index[i]
                                for i in sorted(tool_calls_by_index.keys())
                            ]
                        if usage:
                            message["usage"] = {
                                "prompt_tokens": usage.get("prompt_tokens", 0),
                                "completion_tokens": usage.get("completion_tokens", 0),
                            }
                        yield message
                        break

        except httpx.TimeoutException:
            raise NetworkError("Request to OpenRouter timed out. Try again in a moment")
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
    

def fetch_models() -> list[dict]:
    try:
        response = httpx.get(
            url="https://openrouter.ai/api/v1/models",
            timeout=TIMEOUT
        )

        if response.status_code != 200:
            raise NetworkError(f"OpenRouter returned status {response.status_code}")

        return response.json()["data"]

    except httpx.TimeoutException:
        raise NetworkError("Request to OpenRouter timed out. Try again in a moment")
    except httpx.ConnectError:
        raise NetworkError("Could not reach OpenRouter")
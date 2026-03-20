import os
import re
import json
import logging
import requests
from typing import Dict, Any

from tools.order_tools import get_products, get_order, cancel_order

# Configuration (Can change model)
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL = os.environ.get("OLLAMA_MODEL", "gpt-oss:20b-cloud")

# Tool map and basic schemas
tool_map = {
    "get_products": get_products,
    "get_order": get_order,
    "cancel_order": cancel_order,
}

TOOL_DESCRIPTIONS = {
    "get_products": {
        "description": "Return a list of available products. No args required.",
        "schema": {}
    },
    "get_order": {
        "description": "Return order details given order_id.",
        "schema": {"order_id": "string"}
    },
    "cancel_order": {
        "description": "Cancel an order given order_id.",
        "schema": {"order_id": "string"}
    },
}

# System prompt (keeps consistent instructions to LLM)
SYSTEM_PROMPT = """
You are an AI customer support agent for an ecommerce store.

Your task is to decide whether a tool should be used.

Available tools:

get_products
Use when the user asks about products, items, catalog, or what the store sells.

get_order
Use when the user asks about an order status, tracking an order, or checking an order.

Required argument:
order_id (string)

cancel_order
Use when the user wants to cancel an order.

Required argument:
order_id (string)

CRITICAL RULES

1. If the request relates to products, you MUST call get_products.
2. If the request mentions an order ID and asks about its status, you MUST call get_order.
3. If the request asks to cancel an order, you MUST call cancel_order.
4. Even if the order might not exist, still call the tool. The backend system will handle it.
5. When calling a tool, respond ONLY with JSON.
6. Do NOT include explanations.

Tool format:

{
  "tool": "tool_name",
  "args": {}
}

Examples:

User: show products
{
  "tool": "get_products",
  "args": {}
}

User: what products do you have
{
  "tool": "get_products",
  "args": {}
}

User: where is my order 1001
{
  "tool": "get_order",
  "args": {"order_id": "1001"}
}

User: check order 1002
{
  "tool": "get_order",
  "args": {"order_id": "1002"}
}

User: cancel order 1001
{
  "tool": "cancel_order",
  "args": {"order_id": "1001"}
}

User: please cancel my order 1002
{
  "tool": "cancel_order",
  "args": {"order_id": "1002"}
}

If the user asks a general question not related to store operations, answer normally.
"""

# logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("agent")

# helper functions
def extract_json_from_text(text: str) -> str | None:
    """
    Tries to find a JSON object in a larger string.
    """
    try:
        json.loads(text)
        return text
    except Exception:
        pass

    m = re.search(r"\{.*\}", text, re.DOTALL)

    if m:
        candidate = m.group(0)
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            return None

    return None

def safe_json_loads(text: str) -> Any:
    """
    robust JSON loads: unescape if needed
    """
    s = text.strip()
    # sometimes response is a JSON string e.g. "\"{...}\""
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        try:
            s2 = json.loads(s)  # unescape
            return json.loads(s2)
        except Exception:
            pass
    return json.loads(s)

# LLM call
def call_ollama(prompt: str, model: str = MODEL, timeout: int = 60) -> Dict[str, Any]:
    payload = {
        "model": model,
        "prompt": SYSTEM_PROMPT + "\nUser: " + prompt,
        "stream": False,
    }
    logger.info("Calling Ollama model=%s prompt=%s", model, repr(prompt[:120]))
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    except Exception as e:
        logger.exception("HTTP error calling Ollama")
        return {"ok": False, "error": f"HTTP error: {e}"}

    if r.status_code != 200:
        logger.error("Ollama returned status %s body=%s", r.status_code, r.text[:500])
        # return full response for debugging
        return {"ok": False, "status_code": r.status_code, "body": r.text}

    try:
        data = r.json()
    except Exception:
        logger.exception("Invalid JSON from Ollama: %s", r.text[:800])
        return {"ok": False, "error": "Invalid JSON from Ollama", "body": r.text}

    # Some Ollama responses wrap content under 'response' or nested - be tolerant
    # If 'response' exists and is string, use that. Otherwise try to join parts.
    response_text = None
    if isinstance(data.get("response"), str):
        response_text = data["response"]
    elif isinstance(data.get("response"), dict):
        # sometimes response is {"content":"..."} or similar
        # try common keys
        resp = data["response"]
        for k in ("content", "text", "message"):
            if k in resp and isinstance(resp[k], str):
                response_text = resp[k]
                break
        if response_text is None:
            # fallback: dump it
            response_text = json.dumps(resp)
    else:
        # fallback to raw body
        response_text = json.dumps(data)

    logger.debug("Raw model response: %s", response_text[:800])
    return {"ok": True, "response_text": response_text, "raw": data}

# main agent logic
def interpret_and_call_tools(user_input: str):
    tool = None
    args = {}
    response_text = ""

    # Retry loop (max 2 attempts)
    for attempt in range(2):

        llm_res = call_ollama(user_input)

        if not llm_res.get("ok"):
            logger.warning("LLM call failed attempt=%s", attempt)
            continue

        response_text = llm_res["response_text"]

        # Extract JSON
        json_candidate = extract_json_from_text(response_text)

        if not json_candidate:
            logger.warning("No JSON found in model output attempt=%s", attempt)
            continue

        try:
            parsed = safe_json_loads(json_candidate)
        except Exception as e:
            logger.warning("JSON parse failed attempt=%s error=%s", attempt, e)
            continue

        tool = parsed.get("tool")
        args = parsed.get("args", {}) or {}

        if tool in tool_map:
            logger.info("Model selected tool=%s attempt=%s", tool, attempt)
            break

        logger.info("Invalid tool returned (%s) attempt=%s", tool, attempt)

    # After retry attempts
    if tool not in tool_map:
        logger.warning("Model failed to return valid tool after retries")
        return {"response": {"tool": "none", "args": {}, "raw": response_text}}

    # Auto extract order_id if missing
    if tool in ("get_order", "cancel_order"):
        if "order_id" not in args or not args.get("order_id"):
            match = re.search(r"\b(\d{3,20})\b", user_input)
            if match:
                args["order_id"] = match.group(1)
                logger.info("Auto-extracted order_id=%s", args["order_id"])

    # Execute tool
    try:
        result = tool_map[tool](**args)
        logger.info("Tool %s executed successfully", tool)
        return {"response": result}

    except TypeError as te:
        logger.exception("Tool argument error")
        return {"response": {"error": "tool_argument_error", "details": str(te)}}

    except Exception as e:
        logger.exception("Tool runtime error")
        return {"response": {"error": "tool_runtime_error", "details": str(e)}}
        
# CLI / interactive usage
def run_agent():
    print(f"AI Agent started. Model={MODEL}. Type 'exit' to quit.\n")
    while True:
        user_input = input("User: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        out = interpret_and_call_tools(user_input)
        print("Agent:", json.dumps(out, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    run_agent()
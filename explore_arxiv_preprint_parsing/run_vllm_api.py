import json
import logging
from pathlib import Path
import re
from typing import Optional, Sequence

import requests

LOGGER = logging.getLogger(__name__)

VLLM_BASE_URL = "http://localhost:8000/v1"


FENCED_JSON_RE = re.compile(
    r"```(?:json)?\s*\n(?P<body>[\s\S]*?)\n```",
    re.IGNORECASE,
)


def load_prompt_template(prompt_file: Path) -> str:
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        raise RuntimeError(f"Failed to load prompt template: {e}") from e


def parse_json_output(output: str) -> Optional[Sequence[dict]]:
    try:
        m = FENCED_JSON_RE.search(output)
        # m = re.search(r"```json\n(\[.*\])```", output)
        if not m:
            LOGGER.warning("No json fenced block found in output")
            return None
        body = m.group("body").strip()
        LOGGER.info("body: %r", body)
        return json.loads(body)
    except json.JSONDecodeError:
        LOGGER.warning("Failed to parse JSON")
        return None


def truncate_markdown(text: str, max_chars: int, *, min_tail_window: int = 200) -> str:
    """
    Truncate to <= max_chars.
    Prefer a newline boundary; else whitespace boundary; else hard cut.
    min_tail_window: only consider boundaries in the last N chars of the window
                     to avoid cutting *too* early.
    """
    if len(text) <= max_chars:
        return text

    window = text[:max_chars]

    # Prefer last newline near the end.
    start = max(0, len(window) - min_tail_window)
    nl = window.rfind("\n", start)
    if nl != -1 and nl > 0:
        return window[:nl].rstrip()

    # Fall back to last whitespace (word boundary).
    ws = max(window.rfind(" "), window.rfind("\t"))
    if ws != -1 and ws > 0:
        return window[:ws].rstrip()

    # Worst case: single huge token/word; hard truncate.
    return window.rstrip()


def main() -> None:
    prompt_file = "arxiv-preprint-parsing/benchmarking/benchmarking_lora/prompt.txt"
    markdown_file = "example-data/example-arxiv-papers_md/1109.3792.md"
    system_prompt = load_prompt_template(Path(prompt_file))
    markdown_text = Path(markdown_file).read_text(encoding="utf-8")

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": truncate_markdown(markdown_text, max_chars=2000)}
    ]

    # 3) Send an OpenAI-compatible completion request
    # vLLM’s docs show /v1/completions and /v1/chat/completions usage patterns. [web:168]
    # prompt = "<your prompt here>"

    resp = requests.post(
        f"{VLLM_BASE_URL}/chat/completions",
        json={
            "model": "affiliation-lora",
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 512,
        },
        timeout=300,
    )
    LOGGER.info("resp.status_code: %r", resp.status_code)
    if resp.status_code >= 300:
        LOGGER.info("response text: %r", resp.text)
    resp.raise_for_status()
    data = resp.json()
    LOGGER.info("data: %r", data)
    content = data["choices"][0]["message"]["content"]
    parsed_json_output = parse_json_output(content)
    if not parsed_json_output:
        print(content)
        raise RuntimeError("JSON not found in output")
    # print(data["choices"][0]["message"]["content"])
    print(json.dumps(parsed_json_output, indent=2))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

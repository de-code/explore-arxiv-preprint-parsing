import logging

import requests
from huggingface_hub import snapshot_download

LOGGER = logging.getLogger(__name__)

VLLM_BASE_URL = "http://localhost:8000/v1"


def main() -> None:
    # 1) Download LoRA adapter snapshot to local cache path
    lora_path = snapshot_download(
        repo_id="cometadata/affiliation-parsing-lora-Qwen3-8B-distil-GLM_4.5_Air",
    )

    # 2) Tell vLLM server to load it
    r = requests.post(
        f"{VLLM_BASE_URL}/load_lora_adapter",
        json={
            "lora_name": "affiliation-lora",
            "lora_path": lora_path
        },
        timeout=300,
    )
    if r.status_code >= 300:
        LOGGER.info("response text: %r", r.text)
    r.raise_for_status()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

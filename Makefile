PYTHON = uv run
LINT_MODULES = explore_arxiv_preprint_parsing


dev-flake8:
	$(PYTHON) -m flake8 $(LINT_MODULES)


dev-pylint:
	$(PYTHON) -m pylint $(LINT_MODULES)


dev-mypy:
	$(PYTHON) -m mypy $(LINT_MODULES) $(ARGS)


dev-lint: dev-flake8 dev-pylint dev-mypy


comet-arxiv-results-list-1000-dois:
	cat example-data/comet-arxiv-results-first-1000.jsonl \
		| jq --raw-output .doi


download-example-arxiv-pdfs:
	uv run \
		arxiv-preprint-parsing/utils/download_arxiv_pdfs/download_arxiv_pdfs_from_doi_file_input/download_arxiv_pdfs.py \
		--input_path example-data/example-arxiv-papers.csv


convert-pds-to-markdown:
	uv run \
		 explore_arxiv_preprint_parsing/batch_convert_pdf_to_markdown.py \
		 --input-dir example-data/example-arxiv-papers_pdfs \
		 --output-dir example-data/example-arxiv-papers_md


vllm-serve:
	VLLM_ALLOW_RUNTIME_LORA_UPDATING=True \
		uv run vllm serve Qwen/Qwen3-8B-AWQ \
		--enable-lora \
		--max-model-len 2048 \
		--max-num-seqs 8 \
		--gpu-memory-utilization 0.85 \
		--enforce-eager


vllm-load-lora:
	uv run \
		explore_arxiv_preprint_parsing/vllm_load_lora.py


run-vllm-api:
	uv run \
		explore_arxiv_preprint_parsing/run_vllm_api.py

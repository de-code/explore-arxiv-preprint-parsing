import argparse
import logging
from pathlib import Path

from markitdown import MarkItDown
from tqdm import tqdm


LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-dir",
        required=True,
        help="Input directory containing PDFs"
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Output directory, where markdown files should be stored"
    )
    return parser.parse_args()


def run(
    input_dir: str,
    output_dir: str
) -> None:
    pdf_files = list(Path(input_dir).glob("*.pdf"))
    if not pdf_files:
        raise RuntimeError("No PDFs found")
    LOGGER.debug("files: %r", list(Path(input_dir).glob("*.pdf")))
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(exist_ok=True, parents=True)
    for pdf_path in tqdm(pdf_files):
        md = MarkItDown()
        md_output_path = output_dir_path / pdf_path.with_suffix(".md").name
        result = md.convert(pdf_path)
        md_output_path.write_text(result.text_content, encoding="utf-8")


def main():
    args = parse_args()
    LOGGER.info("args: %r", args)
    run(
        input_dir=args.input_dir,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

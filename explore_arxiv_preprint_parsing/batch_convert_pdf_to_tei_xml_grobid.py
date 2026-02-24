import argparse
import logging
from pathlib import Path

import requests
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
        help="Output directory, where TEI XML files should be stored"
    )
    parser.add_argument(
        "--endpoint-url",
        default="http://localhost:8080/api/processHeaderDocument"
    )
    return parser.parse_args()


def convert_pdf_to_tei_xml(
    pdf_path: Path,
    tei_xml_output_path: Path,
    endpoint_url: str
) -> None:
    with requests.Session() as session:
        with pdf_path.open(mode="rb") as pdf_fp:
            response = session.post(
                url=endpoint_url,
                files={
                    "input": pdf_fp
                }
            )
            response.raise_for_status()
            tei_xml_output_path.write_text(
                response.text,
                encoding="utf-8"
            )


def run(
    input_dir: str,
    output_dir: str,
    endpoint_url: str
) -> None:
    pdf_files = list(Path(input_dir).glob("*.pdf"))
    if not pdf_files:
        raise RuntimeError("No PDFs found")
    LOGGER.debug("files: %r", list(Path(input_dir).glob("*.pdf")))
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(exist_ok=True, parents=True)
    failed_pdf_paths: list[str] = []
    last_exc: Exception | None = None
    for pdf_path in tqdm(pdf_files):
        tei_xml_output_path = output_dir_path / pdf_path.with_suffix(".tei.xml").name
        if tei_xml_output_path.exists():
            LOGGER.info("skipping already converted: %r", tei_xml_output_path.name)
            continue
        try:
            convert_pdf_to_tei_xml(
                pdf_path=pdf_path,
                tei_xml_output_path=tei_xml_output_path,
                endpoint_url=endpoint_url
            )
        except Exception as exc:
            last_exc = exc
            failed_pdf_paths.append(str(pdf_path))
            LOGGER.warning("Failed to process %r due to %r", str(pdf_path), exc)
    if last_exc is not None:
        raise RuntimeError(
            f"Failed to process some PDF: {failed_pdf_paths} due to {repr(last_exc)}"
        ) from last_exc


def main():
    args = parse_args()
    LOGGER.info("args: %r", args)
    run(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        endpoint_url=args.endpoint_url
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

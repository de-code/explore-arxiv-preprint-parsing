import argparse
import csv
import json
import logging
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from tqdm import tqdm


LOGGER = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-csv",
        required=True,
        help="Input CSV"
    )
    parser.add_argument(
        "--tei-xml-dir",
        required=True,
        help="Input directory containing TEI XML files"
    )
    parser.add_argument(
        "--output-file",
        required=True,
        help="Output file for the JSONL file containing results"
    )
    return parser.parse_args()


def get_arxiv_id_from_doi(doi: str):
    m = re.search(r"arxiv\.(.+)(?:\.pdf)?$", doi.lower())
    if not m:
        raise ValueError(f"Unable to extract arxiv id from doi: {doi}")
    return m.group(1)


def get_arxiv_id_filename_from_doi(doi: str):
    arxiv_id = get_arxiv_id_from_doi(doi)
    return arxiv_id.replace("/", "_")



TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}


def parse_authors_with_affiliations(tei_xml: str) -> list[dict]:
    root = ET.fromstring(tei_xml)

    prediction: list[dict] = []
    for author in root.findall(".//tei:analytic/tei:author", TEI_NS):
        # Skip dummy/orphan affiliations
        if author.find("./tei:note[@type='dummy_author']", TEI_NS) is not None:
            continue

        pers = author.find("./tei:persName", TEI_NS)
        if pers is None:
            continue

        first = (pers.findtext("./tei:forename[@type='first']", default="", namespaces=TEI_NS) or "").strip()
        surname = (pers.findtext("./tei:surname", default="", namespaces=TEI_NS) or "").strip()
        name = " ".join(x for x in [first, surname] if x)
        if not name:
            continue

        raw_aff = ""
        aff = author.find("./tei:affiliation", TEI_NS)
        LOGGER.debug("Found tei:aff: %r", aff is not None)
        if aff is not None:
            raw_aff_note = aff.find("./tei:note[@type='raw_affiliation']", namespaces=TEI_NS)
            LOGGER.debug("Found raw_affiliation: %r", raw_aff_note is not None)
            if raw_aff_note is not None:
                LOGGER.debug("Found raw_affiliation: %r", raw_aff_note is not None)
                raw_aff = "".join(raw_aff_note.itertext()).strip()

        prediction.append({
            "name": name,
            "affiliations": ([] if not raw_aff else [{"affiliation": raw_aff, "ror_id": None}]),
        })

    return prediction


def convert_tei_xml_to_authors_affiliation_json(
    tei_xml_file_path: Path
) -> list[dict]:
    return parse_authors_with_affiliations(
        tei_xml_file_path.read_text(encoding="utf-8")
    )


def run(
    input_csv: str,
    tei_xml_dir: str,
    output_file: str
) -> None:
    with open(input_csv, "rt", encoding="utf-8") as input_csv_fp:
        records = list(csv.DictReader(input_csv_fp))
    LOGGER.info("records: %r", records)
    with open(output_file, "wb") as output_fp:
        for record in tqdm(records):
            doi = record["doi"]
            arxiv_id = get_arxiv_id_from_doi(doi)
            arxiv_id_filename = get_arxiv_id_filename_from_doi(doi)
            LOGGER.debug("arxiv_id_filename: %r", arxiv_id_filename)
            tei_xml_file_path = Path(tei_xml_dir) / (arxiv_id_filename + ".tei.xml")
            if not tei_xml_file_path.exists():
                raise RuntimeError(f"TEI XMl file missing: {tei_xml_file_path}")
            result_json = {
                "arxiv_id": f"arXiv:{arxiv_id}",
                "doi": doi,
                "prediction": convert_tei_xml_to_authors_affiliation_json(
                    tei_xml_file_path
                )
            }
            LOGGER.debug("result_json: %r", result_json)
            output_fp.write(json.dumps(result_json).encode("utf-8"))
            output_fp.write(b"\n")


def main():
    args = parse_args()
    LOGGER.info("args: %r", args)
    run(
        input_csv=args.input_csv,
        tei_xml_dir=args.tei_xml_dir,
        output_file=args.output_file
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()

import argparse
from pathlib import Path

from rag_hopital.etl.convert import convert_corpus

parser = argparse.ArgumentParser()
parser.add_argument("--limit", type=int, default=None)
args = parser.parse_args()

convert_corpus(
    source_dir=Path("data/hopital"),
    output_dir=Path("data/conversions"),
    limit=args.limit,
)
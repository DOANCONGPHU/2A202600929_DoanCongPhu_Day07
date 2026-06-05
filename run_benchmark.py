from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import OPENAI_EMBEDDING_MODEL, OpenAIEmbedder
from src.models import Document
from src.store import EmbeddingStore


@dataclass
class BenchmarkCase:
    number: int
    query: str
    gold_answer: str
    source: str
    metadata_filter: dict[str, str]


def configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def split_markdown_row(line: str) -> list[str]:
    return [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]


def parse_metadata_filter(raw_filter: str) -> dict[str, str]:
    match = re.search(r"([A-Za-z_][\w-]*)\s*=\s*([\w-]+)", raw_filter)
    if not match:
        return {}
    return {match.group(1): match.group(2)}


def load_benchmark(path: Path) -> list[BenchmarkCase]:
    lines = path.read_text(encoding="utf-8").splitlines()
    cases: list[BenchmarkCase] = []
    in_table = False

    for line in lines:
        if line.startswith("| # | Query | Gold Answer | File nguồn |"):
            in_table = True
            continue
        if not in_table:
            continue
        if line.startswith("|---"):
            continue
        if not line.startswith("|"):
            if cases:
                break
            continue

        cells = split_markdown_row(line)
        if len(cells) < 5 or not cells[0].isdigit():
            continue
        cases.append(
            BenchmarkCase(
                number=int(cells[0]),
                query=cells[1],
                gold_answer=cells[2],
                source=cells[3],
                metadata_filter=parse_metadata_filter(cells[4]),
            )
        )

    return cases


def build_chunker(name: str):
    if name == "fixed":
        return FixedSizeChunker(chunk_size=500, overlap=50)
    if name == "recursive":
        return RecursiveChunker(chunk_size=500)
    return SentenceChunker(max_sentences_per_chunk=3)


def load_documents(cases: list[BenchmarkCase], chunker) -> list[Document]:
    file_to_category: dict[str, str] = {}
    for case in cases:
        category = case.metadata_filter.get("category")
        if category:
            file_to_category[case.source] = category

    docs: list[Document] = []
    for source in sorted({case.source for case in cases}):
        path = Path("data") / source
        text = path.read_text(encoding="utf-8")
        chunks = chunker.chunk(text)
        for index, chunk in enumerate(chunks):
            docs.append(
                Document(
                    id=f"{path.stem}_{index}",
                    content=chunk,
                    metadata={
                        "source": source,
                        "category": file_to_category.get(source, ""),
                        "chunk_index": index,
                    },
                )
            )
    return docs


def score_by_expected_source(case: BenchmarkCase, results: list[dict]) -> int:
    for index, result in enumerate(results):
        if result["metadata"].get("source") == case.source:
            return 2 if index == 0 else 1
    return 0


def main() -> int:
    configure_console()
    load_dotenv()
    parser = argparse.ArgumentParser(description="Run retrieval benchmark from data/benchmark.md.")
    parser.add_argument("--benchmark", default="data/benchmark.md", help="Benchmark markdown file.")
    parser.add_argument("--chunker", choices=["sentence", "fixed", "recursive"], default="sentence")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--use-filter", action="store_true", help="Apply metadata_filter from benchmark rows.")
    parser.add_argument("--embedding-model", default=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
    args = parser.parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("Thiếu OPENAI_API_KEY trong file .env hoặc biến môi trường.")
        return 1

    cases = load_benchmark(Path(args.benchmark))
    chunker = build_chunker(args.chunker)
    docs = load_documents(cases, chunker)

    print(f"Benchmark: {args.benchmark}")
    print(f"Chunker: {args.chunker}")
    print(f"Use metadata filter: {args.use_filter}")
    print(f"Embedding model: {args.embedding_model}")
    print(f"Stored chunks: {len(docs)}")

    store = EmbeddingStore(collection_name=f"benchmark_{args.chunker}", embedding_fn=OpenAIEmbedder(args.embedding_model))
    store.add_documents(docs)

    total = 0
    for case in cases:
        if args.use_filter and case.metadata_filter:
            results = store.search_with_filter(case.query, top_k=args.top_k, metadata_filter=case.metadata_filter)
        else:
            results = store.search(case.query, top_k=args.top_k)

        case_score = score_by_expected_source(case, results)
        total += case_score

        print("\n" + "=" * 100)
        print(f"CASE {case.number}: {case.query}")
        print(f"Expected source: {case.source}")
        print(f"Gold answer: {case.gold_answer}")
        print(f"Source score: {case_score}/2")
        for index, result in enumerate(results, start=1):
            source = result["metadata"].get("source")
            category = result["metadata"].get("category")
            chunk_index = result["metadata"].get("chunk_index")
            preview = result["content"][:900].replace("\n", " ")
            print(f"\nTOP {index} | source={source} | category={category} | chunk={chunk_index} | score={result['score']:.4f}")
            print(preview)

    print("\n" + "=" * 100)
    print(f"TOTAL SOURCE SCORE: {total}/10")
    print("Gợi ý chấm report: giữ điểm này nếu các chunk top-3 chứa đủ ý của Gold Answer; giảm điểm nếu đúng file nhưng sai đoạn.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

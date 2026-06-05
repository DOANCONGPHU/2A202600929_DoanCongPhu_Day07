from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from src.agent import KnowledgeBaseAgent
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import OPENAI_EMBEDDING_MODEL, OpenAIEmbedder
from src.models import Document
from src.store import EmbeddingStore


DEFAULT_FILES = [
    Path("data/baomatcanhan.md"),
    Path("data/chinhsachbaomat.md"),
    Path("data/dieukhoandatcoc.md"),
]

DEFAULT_QUESTIONS = [
    "Hệ thống thu thập những thông tin cá nhân nào của người dùng?",
    "Thông tin cá nhân của người dùng được bảo vệ như thế nào?",
    "Người dùng có quyền gì đối với dữ liệu cá nhân của mình?",
    "Khi nào khách hàng được hoàn lại tiền đặt cọc?",
    "Trường hợp nào khách hàng có thể mất tiền đặt cọc?",
]


def configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def build_chunker(name: str):
    if name == "fixed":
        return FixedSizeChunker(chunk_size=500, overlap=50)
    if name == "recursive":
        return RecursiveChunker(chunk_size=500)
    return SentenceChunker(max_sentences_per_chunk=3)


def load_chunked_documents(file_paths: list[Path], chunker) -> list[Document]:
    docs: list[Document] = []
    for path in file_paths:
        if not path.exists():
            raise FileNotFoundError(f"Không tìm thấy file: {path}")

        text = path.read_text(encoding="utf-8")
        chunks = chunker.chunk(text)
        for index, chunk in enumerate(chunks):
            docs.append(
                Document(
                    id=f"{path.stem}_{index}",
                    content=chunk,
                    metadata={"source": path.name, "chunk_index": index},
                )
            )
    return docs


def make_llm(model: str):
    client = OpenAI()

    def real_llm(prompt: str) -> str:
        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Bạn là trợ lý trả lời dựa trên tài liệu được cung cấp. "
                        "Trả lời ngắn gọn, rõ ràng bằng tiếng Việt. "
                        "Nếu tài liệu không đủ thông tin, hãy nói rõ là chưa đủ thông tin."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content or ""

    return real_llm


def print_context(store: EmbeddingStore, question: str, top_k: int) -> None:
    results = store.search(question, top_k=top_k)
    print("\nRETRIEVED CONTEXT:")
    for index, result in enumerate(results, start=1):
        source = result["metadata"].get("source", "unknown")
        score = result["score"]
        preview = result["content"][:700].replace("\n", " ")
        print(f"\nTOP {index} | source={source} | score={score:.4f}")
        print(preview)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ask a RAG bot over the selected lab documents.")
    parser.add_argument(
        "--chunker",
        choices=["sentence", "fixed", "recursive"],
        default="sentence",
        help="Chunking strategy to test. Default: sentence.",
    )
    parser.add_argument("--top-k", type=int, default=3, help="Number of retrieved chunks. Default: 3.")
    parser.add_argument("--show-context", action="store_true", help="Print retrieved chunks before each answer.")
    parser.add_argument("--interactive", action="store_true", help="Ask your own questions in a loop.")
    parser.add_argument("--benchmark", action="store_true", help="Run the 5 default benchmark questions.")
    parser.add_argument("--question", action="append", help="Question to ask. Can be used multiple times.")
    parser.add_argument("--file", action="append", help="Document file to include. Can be used multiple times.")
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini"),
        help="OpenAI chat model. Default: env OPENAI_CHAT_MODEL or gpt-4.1-mini.",
    )
    parser.add_argument(
        "--embedding-model",
        default=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL),
        help="OpenAI embedding model. Default: env OPENAI_EMBEDDING_MODEL or text-embedding-3-small.",
    )
    return parser.parse_args()


def main() -> int:
    configure_console()
    load_dotenv()
    args = parse_args()

    if not os.getenv("OPENAI_API_KEY"):
        print("Thiếu OPENAI_API_KEY trong file .env hoặc biến môi trường.")
        return 1

    file_paths = [Path(file_path) for file_path in args.file] if args.file else DEFAULT_FILES
    chunker = build_chunker(args.chunker)
    docs = load_chunked_documents(file_paths, chunker)

    print(f"Chunker: {args.chunker}")
    print(f"Files: {', '.join(path.name for path in file_paths)}")
    print(f"Stored chunks: {len(docs)}")
    print(f"Embedding model: {args.embedding_model}")
    print(f"Chat model: {args.model}")

    embedder = OpenAIEmbedder(model_name=args.embedding_model)
    store = EmbeddingStore(collection_name=f"bot_{args.chunker}", embedding_fn=embedder)
    store.add_documents(docs)
    agent = KnowledgeBaseAgent(store=store, llm_fn=make_llm(args.model))

    if args.interactive or (not args.question and not args.benchmark):
        print("\nBạn có thể tự hỏi bot ở đây.")
        print("Gõ câu hỏi rồi nhấn Enter. Gõ 'exit' để thoát.")
        while True:
            question = input("\nBạn hỏi: ").strip()
            if question.lower() in {"exit", "quit", "q"}:
                break
            if not question:
                continue
            if args.show_context:
                print_context(store, question, args.top_k)
            print("\nANSWER:")
            print(agent.answer(question, top_k=args.top_k))
        return 0

    questions = args.question or DEFAULT_QUESTIONS
    for question in questions:
        print("\n" + "=" * 80)
        print("QUESTION:", question)
        if args.show_context:
            print_context(store, question, args.top_k)
        print("\nANSWER:")
        print(agent.answer(question, top_k=args.top_k))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

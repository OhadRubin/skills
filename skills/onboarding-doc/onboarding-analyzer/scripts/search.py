# /// script
# dependencies = [
#   "bm25s",
#   "PyStemmer",
# ]
# ///

import argparse
import os
import sys
from pathlib import Path

import bm25s
import Stemmer


def index_command(args):
    """Index files from a directory."""
    directory = Path(args.directory)
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    # Collect files
    corpus = []
    file_paths = []

    patterns = args.patterns.split(",") if args.patterns else ["*.md", "*.py", "*.txt"]

    for pattern in patterns:
        for file_path in directory.rglob(pattern.strip()):
            if file_path.is_file():
                try:
                    content = file_path.read_text(encoding="utf-8")
                    corpus.append(content)
                    file_paths.append(str(file_path))
                except Exception as e:
                    print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)

    if not corpus:
        raise ValueError(f"No files found in {directory} matching patterns: {patterns}")

    print(f"Indexing {len(corpus)} files...")

    # Tokenize and index
    stemmer = Stemmer.Stemmer("english")
    corpus_tokens = bm25s.tokenize(corpus, stopwords="en", stemmer=stemmer)

    retriever = bm25s.BM25()
    retriever.index(corpus_tokens)

    # Save index and file paths
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    retriever.save(str(output_dir), corpus=file_paths)

    print(f"Index saved to {output_dir}")
    print(f"Indexed {len(corpus)} files")


def search_command(args):
    """Search the index."""
    terms = args.term

    # Validate: each term must be a single word (no spaces)
    for term in terms:
        if " " in term:
            raise ValueError(f"Each term must be a single word without spaces. Got: '{term}'")

    index_dir = Path(args.index)
    if not index_dir.exists():
        raise FileNotFoundError(f"Index not found: {index_dir}")

    # Load index
    retriever = bm25s.BM25.load(str(index_dir), load_corpus=True)
    file_paths = retriever.corpus  # file paths stored as corpus

    # Concatenate terms into query
    query = " ".join(terms)

    # Tokenize query
    stemmer = Stemmer.Stemmer("english")
    query_tokens = bm25s.tokenize(query, stemmer=stemmer)

    # Search - pass corpus to get documents directly
    k = min(args.top_k, len(file_paths))
    results, scores = retriever.retrieve(query_tokens, corpus=file_paths, k=k)

    print(f"Terms: {terms}")
    print(f"Query: {query}\n")
    found = 0
    for i in range(results.shape[1]):
        result = results[0, i]
        score = scores[0, i]
        if score > 0:
            # result is a dict with 'id' and 'text' when corpus is passed
            if isinstance(result, dict):
                file_path = result.get("text", str(result))
            else:
                file_path = str(result)
            print(f"Rank {i+1} (score: {score:.2f}): {file_path}")
            found += 1

    if found == 0:
        print(f"No results found for terms {terms}. Try more general terms.")


def main():
    parser = argparse.ArgumentParser(
        description="BM25 search tool for onboarding documentation"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Index command
    index_parser = subparsers.add_parser("index", help="Index files from a directory")
    index_parser.add_argument("directory", help="Directory to index")
    index_parser.add_argument(
        "-o", "--output",
        default=".bm25_index",
        help="Output directory for index (default: .bm25_index)"
    )
    index_parser.add_argument(
        "-p", "--patterns",
        default="*.md,*.py,*.txt",
        help="Comma-separated glob patterns (default: *.md,*.py,*.txt)"
    )
    index_parser.set_defaults(func=index_command)

    # Search command
    search_parser = subparsers.add_parser("search", help="Search the index")
    search_parser.add_argument(
        "-t", "--term",
        action="append",
        required=True,
        help="Search term (no spaces). Can be repeated: -t auth -t token"
    )
    search_parser.add_argument(
        "-i", "--index",
        default=".bm25_index",
        help="Index directory (default: .bm25_index)"
    )
    search_parser.add_argument(
        "-k", "--top-k",
        type=int,
        default=5,
        help="Number of results to return (default: 5)"
    )
    search_parser.set_defaults(func=search_command)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

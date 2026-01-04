# /// script
# dependencies = [
#   "bm25s",
#   "PyStemmer",
# ]
# ///

import argparse
import subprocess
import sys
from pathlib import Path

import bm25s
import Stemmer


def main():
    parser = argparse.ArgumentParser(
        description="BM25 search over git-tracked files"
    )
    parser.add_argument(
        "-t", "--term",
        action="append",
        required=True,
        help="Search term (no spaces). Can be repeated: -t auth -t token"
    )
    parser.add_argument(
        "-k", "--top-k",
        type=int,
        default=10,
        help="Number of results to return (default: 10)"
    )
    args = parser.parse_args()

    terms = args.term

    # Validate: each term must be a single word (no spaces)
    for term in terms:
        if " " in term:
            raise ValueError(f"Each term must be a single word without spaces. Got: '{term}'")

    # Get files from git ls-files
    result = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True,
        check=True
    )
    file_paths = [f for f in result.stdout.strip().split("\n") if f]

    if not file_paths:
        raise ValueError("No files found in git repository")

    # Read file contents
    corpus = []
    valid_paths = []
    for file_path in file_paths:
        path = Path(file_path)
        if path.is_file():
            try:
                content = path.read_text(encoding="utf-8")
                corpus.append(content)
                valid_paths.append(file_path)
            except Exception:
                pass  # Skip binary/unreadable files

    if not corpus:
        raise ValueError("No readable files found")

    # Index
    stemmer = Stemmer.Stemmer("english")
    corpus_tokens = bm25s.tokenize(corpus, stopwords="en", stemmer=stemmer)
    retriever = bm25s.BM25()
    retriever.index(corpus_tokens)

    # Search
    query = " ".join(terms)
    query_tokens = bm25s.tokenize(query, stemmer=stemmer)

    k = min(args.top_k, len(valid_paths))
    results, scores = retriever.retrieve(query_tokens, corpus=valid_paths, k=k)

    print(f"Terms: {terms}\n")
    found = 0
    for i in range(results.shape[1]):
        result = results[0, i]
        score = scores[0, i]
        if score > 0:
            if isinstance(result, dict):
                file_path = result.get("text", str(result))
            else:
                file_path = str(result)
            print(f"{score:.2f}  {file_path}")
            found += 1

    if found == 0:
        print("No results found. Try more general terms.")


if __name__ == "__main__":
    main()

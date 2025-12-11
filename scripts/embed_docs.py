#!/usr/bin/env python3
"""
Embed documentation and upload to Supabase.

Usage:
    uv run python scripts/embed_docs.py

Requires:
    - OPENAI_API_KEY env var (or in docs-site/.env.local)
    - NEXT_PUBLIC_SUPABASE_URL env var (or in docs-site/.env.local)
    - NEXT_PUBLIC_SUPABASE_ANON_KEY env var (or in docs-site/.env.local)
"""

import os
import re
from pathlib import Path

# Load env from docs-site/.env.local if not already set
env_file = Path(__file__).parent.parent / "docs-site" / ".env.local"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                if key not in os.environ:
                    os.environ[key] = value

# Now import after env is loaded
try:
    import openai
    from supabase import Client, create_client
except ImportError:
    print("Installing required packages...")
    import subprocess  # nosec B404

    subprocess.run(  # nosec B603, B607
        ["uv", "pip", "install", "openai", "supabase"], check=True
    )
    import openai
    from supabase import Client, create_client

# Configuration
DOCS_DIR = Path(__file__).parent.parent / "docs"
CHUNK_SIZE = 500  # tokens (approximate)
CHUNK_OVERLAP = 50


def get_openai_client() -> openai.OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment")
    return openai.OpenAI(api_key=api_key)


def get_supabase_client() -> Client:
    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    # Prefer service key for write operations, fall back to anon
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get(
        "NEXT_PUBLIC_SUPABASE_ANON_KEY"
    )
    if not url or not key:
        raise ValueError("Supabase credentials not found in environment")
    return create_client(url, key)


def extract_title(content: str, filename: str) -> str:
    """Extract title from frontmatter or first heading."""
    # Try frontmatter
    frontmatter_match = re.search(
        r"^---\s*\n.*?title:\s*['\"]?(.+?)['\"]?\s*\n.*?---", content, re.DOTALL
    )
    if frontmatter_match:
        return frontmatter_match.group(1).strip()

    # Try first h1
    h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if h1_match:
        return h1_match.group(1).strip()

    # Fallback to filename
    return filename.replace("-", " ").replace("_", " ").title()


def clean_content(content: str) -> str:
    """Remove frontmatter and clean markdown."""
    # Remove frontmatter
    content = re.sub(r"^---\s*\n.*?---\s*\n", "", content, flags=re.DOTALL)
    # Remove Jekyll liquid tags
    content = re.sub(r"\{%.*?%\}", "", content)
    content = re.sub(r"\{\{.*?\}\}", "", content)
    # Remove HTML comments
    content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
    # Remove excessive whitespace
    content = re.sub(r"\n{3,}", "\n\n", content)
    return content.strip()


def chunk_text(
    text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP
) -> list[str]:
    """Split text into overlapping chunks."""
    # Approximate tokens as words * 1.3
    words = text.split()
    tokens_per_chunk = int(chunk_size / 1.3)
    overlap_words = int(overlap / 1.3)

    chunks = []
    start = 0

    while start < len(words):
        end = min(start + tokens_per_chunk, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start = end - overlap_words

        if start >= len(words) - overlap_words:
            break

    return chunks


def get_embedding(client: openai.OpenAI, text: str) -> list[float]:
    """Get embedding from OpenAI."""
    response = client.embeddings.create(model="text-embedding-ada-002", input=text)
    return response.data[0].embedding


def get_slug_from_path(filepath: Path, docs_dir: Path) -> str:
    """Convert filepath to URL slug."""
    relative = filepath.relative_to(docs_dir)
    slug = str(relative).replace(".md", "").replace("\\", "/")

    # Handle index files
    if slug == "index":
        return ""
    if slug.endswith("/index"):
        return slug[:-6]

    return slug


def main() -> None:
    print("Embedding Fabra documentation...")

    # Initialize clients
    openai_client = get_openai_client()
    supabase = get_supabase_client()

    # Find all markdown files
    md_files = list(DOCS_DIR.glob("**/*.md"))
    print(f"Found {len(md_files)} markdown files")

    # Clear existing embeddings
    print("Clearing existing embeddings...")
    supabase.table("doc_embeddings").delete().neq("id", 0).execute()

    total_chunks = 0

    for filepath in md_files:
        # Skip hidden files and certain directories
        if any(part.startswith("_") or part.startswith(".") for part in filepath.parts):
            continue

        print(f"Processing: {filepath.name}")

        content = filepath.read_text(encoding="utf-8")
        title = extract_title(content, filepath.stem)
        clean = clean_content(content)

        if not clean:
            print(f"  Skipping empty file: {filepath.name}")
            continue

        slug = get_slug_from_path(filepath, DOCS_DIR)
        chunks = chunk_text(clean)

        print(f"  Title: {title}")
        print(f"  Slug: {slug or '(index)'}")
        print(f"  Chunks: {len(chunks)}")

        for i, chunk in enumerate(chunks):
            embedding = get_embedding(openai_client, chunk)

            supabase.table("doc_embeddings").upsert(
                {
                    "slug": slug,
                    "title": title,
                    "chunk_index": i,
                    "content": chunk[:2000],  # Limit content size
                    "embedding": embedding,
                }
            ).execute()

            total_chunks += 1

        print(f"  Uploaded {len(chunks)} chunks")

    print(f"\nDone! Uploaded {total_chunks} total chunks.")


if __name__ == "__main__":
    main()

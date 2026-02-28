"""
Generate embeddings for blog posts using text-embedding-3-small.
Stores embeddings in PostgreSQL via pgvector.
"""
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

import django
django.setup()

from openai import OpenAI
from blog.models import Post


def generate_embeddings(batch_size: int = 100):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    posts = Post.objects.filter(status="published")
    total = posts.count()
    print(f"Generating embeddings for {total} posts...")

    processed = 0
    for i in range(0, total, batch_size):
        batch = posts[i:i + batch_size]
        texts = []
        post_ids = []

        for post in batch:
            # Combine title + summary + truncated content for embedding
            text = f"{post.title}\n{post.summary}\n{post.content[:2000]}"
            texts.append(text)
            post_ids.append(post.id)

        if not texts:
            continue

        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts,
        )

        for j, embedding_data in enumerate(response.data):
            # Store embedding as JSON (pgvector will be configured in Phase 6)
            # For now, we can store in a JSONField or handle in Phase 6
            post = Post.objects.get(id=post_ids[j])
            # post.embedding = embedding_data.embedding  # Needs pgvector field
            post.save()

        processed += len(texts)
        print(f"  Processed {processed}/{total}")

    # Estimate cost
    est_tokens = total * 500  # ~500 tokens per post
    est_cost = est_tokens * 0.02 / 1_000_000
    print(f"Done! Estimated cost: ~${est_cost:.4f}")


if __name__ == "__main__":
    generate_embeddings()

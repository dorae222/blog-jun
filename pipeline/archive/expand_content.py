#!/usr/bin/env python3
"""
Expand content.json files for 37 LLM architecture blog posts.
Reads content from individual .md files in pipeline/expanded_content/ dir.
"""
import json
import os
import re
import sys

BASE_DIR = "/Users/dorae222/Documents/Obsidian/blog-jun/pipeline/data/architectures_written"
CONTENT_DIR = "/Users/dorae222/Documents/Obsidian/blog-jun/pipeline/expanded_content"

def get_related_docs_section(content):
    """Extract the ## 관련 문서 section from existing content."""
    match = re.search(r'(## 관련 문서\s*\n.*)', content, re.DOTALL)
    if match:
        return match.group(1).strip()
    return None

def count_words(text):
    return len(text.split())

def process_model(slug):
    """Process a single model: read expanded .md, update content.json."""
    md_path = os.path.join(CONTENT_DIR, f"{slug}.md")
    content_path = os.path.join(BASE_DIR, slug, "content.json")

    if not os.path.exists(md_path):
        print(f"  SKIP {slug}: no expanded content file")
        return None
    if not os.path.exists(content_path):
        print(f"  SKIP {slug}: content.json not found")
        return None

    # Read expanded content
    with open(md_path, "r", encoding="utf-8") as f:
        new_content = f.read().strip()

    # Read existing content.json
    with open(content_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    existing_content = data.get("content", "")

    # Preserve existing related docs section if new content doesn't have one
    existing_related = get_related_docs_section(existing_content)
    new_related = get_related_docs_section(new_content)

    if existing_related and not new_related:
        new_content = new_content.rstrip() + "\n\n" + existing_related + "\n"

    # Update content field only
    data["content"] = new_content

    # Write back
    with open(content_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    wc = count_words(new_content)
    print(f"  {slug}: {wc} words")
    return wc

def main():
    slugs = [
        "chinchilla", "cohere-command-a", "deepseek-v3", "distilbert", "electra",
        "elmo", "ernie", "gopher", "gpt-2", "gpt-4", "gpt-4-1", "gpt-5",
        "gpt-5-2", "grok-3", "instructgpt", "jamba", "jamba-1-6", "kimi-k2",
        "kimi-k2-5", "llama", "llama-2", "llama-3", "llama-4", "mistral-7b",
        "mistral-large-3", "mt5", "o3", "o4-mini", "olmo", "phi", "phi-3",
        "phi-4-reasoning", "qwen3", "qwen3-5", "switch-transformer", "t5", "yi"
    ]

    processed = 0
    skipped = 0
    for slug in slugs:
        wc = process_model(slug)
        if wc is not None:
            processed += 1
        else:
            skipped += 1

    print(f"\nDone: {processed} processed, {skipped} skipped")

if __name__ == "__main__":
    main()

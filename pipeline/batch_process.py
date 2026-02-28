"""
OpenAI Batch API processor.
Reuses the pattern from batch-explanation-generator.
"""
import os
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DATA_DIR = Path(__file__).parent / "data"
BATCH_INPUT_FILE = DATA_DIR / "batch_input.jsonl"
BATCH_OUTPUT_FILE = DATA_DIR / "batch_output.jsonl"
BATCH_ID_FILE = DATA_DIR / "batch_id.txt"


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set. Create a .env file.")
    return OpenAI(api_key=api_key)


def upload_and_create_batch(client: OpenAI) -> str:
    print(f"Uploading {BATCH_INPUT_FILE}...")
    with open(BATCH_INPUT_FILE, "rb") as f:
        batch_file = client.files.create(file=f, purpose="batch")
    print(f"File uploaded: {batch_file.id}")

    batch = client.batches.create(
        input_file_id=batch_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"description": "blog-jun content refinement"},
    )
    print(f"Batch created: {batch.id}")

    BATCH_ID_FILE.write_text(batch.id)
    return batch.id


def wait_for_batch(client: OpenAI, batch_id: str, poll_interval: int = 60):
    print(f"Waiting for batch {batch_id}...")
    while True:
        batch = client.batches.retrieve(batch_id)
        status = batch.status
        counts = batch.request_counts

        if counts:
            print(f"  Status: {status} | Completed: {counts.completed}/{counts.total} | Failed: {counts.failed}")
        else:
            print(f"  Status: {status}")

        if status == "completed":
            return batch
        elif status in ("failed", "expired", "cancelled"):
            raise Exception(f"Batch {status}: {batch_id}")

        time.sleep(poll_interval)


def download_results(client: OpenAI, batch):
    if not batch.output_file_id:
        raise Exception("No output file")

    result = client.files.content(batch.output_file_id)
    BATCH_OUTPUT_FILE.write_text(result.text, encoding="utf-8")

    lines = BATCH_OUTPUT_FILE.read_text().strip().split("\n")
    print(f"Downloaded {len(lines)} results → {BATCH_OUTPUT_FILE}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--batch-id", type=str)
    args = parser.parse_args()

    client = get_client()
    batch_id = args.batch_id or (BATCH_ID_FILE.read_text().strip() if BATCH_ID_FILE.exists() else None)

    if args.status:
        if batch_id:
            batch = client.batches.retrieve(batch_id)
            print(f"ID: {batch.id}, Status: {batch.status}")
            if batch.request_counts:
                print(f"  Total: {batch.request_counts.total}, Completed: {batch.request_counts.completed}, Failed: {batch.request_counts.failed}")
        return

    if args.resume:
        if not batch_id:
            print("No batch ID to resume")
            return
    else:
        batch_id = upload_and_create_batch(client)

    batch = wait_for_batch(client, batch_id)
    download_results(client, batch)
    print("Done! Run batch_import.py next.")


if __name__ == "__main__":
    main()

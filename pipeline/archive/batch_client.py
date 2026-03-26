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


def upload_and_create_batch(client: OpenAI, input_file: Path) -> str:
    print(f"Uploading {input_file}...")
    with open(input_file, "rb") as f:
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


def download_results(client: OpenAI, batch, output_file: Path = None):
    if not batch.output_file_id:
        raise Exception("No output file")

    result = client.files.content(batch.output_file_id)
    dest = output_file if output_file else BATCH_OUTPUT_FILE
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(result.text, encoding="utf-8")

    lines = dest.read_text().strip().split("\n")
    print(f"Downloaded {len(lines)} results → {dest}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--batch-id", type=str)
    parser.add_argument("--test", action="store_true", help="테스트 모드: batch_input_test.jsonl 사용 (5건)")
    parser.add_argument("--input", type=str, help="입력 JSONL 파일 경로 지정")
    parser.add_argument("--output", type=str, help="출력 JSONL 파일 경로 지정")
    args = parser.parse_args()

    # 입력 파일 결정
    if args.test:
        input_file = DATA_DIR / "batch_input_test.jsonl"
    elif args.input:
        input_file = Path(args.input)
    else:
        input_file = BATCH_INPUT_FILE

    if not args.resume and not args.status and not input_file.exists():
        print(f"Input file not found: {input_file}")
        return

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
        print(f"Mode: {'TEST' if args.test else 'FULL'} | Input: {input_file}")
        batch_id = upload_and_create_batch(client, input_file)

    output_file = Path(args.output) if args.output else None
    batch = wait_for_batch(client, batch_id)
    download_results(client, batch, output_file)
    print("Done! Run batch_import.py next.")


if __name__ == "__main__":
    main()

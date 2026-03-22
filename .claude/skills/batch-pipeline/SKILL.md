---
name: batch-pipeline
description: OpenAI Batch API 파이프라인 실행 (prepare → process → import)
allowed-tools: Bash(python *), Read, Glob
---
Batch API 3단계 파이프라인:

1. Prepare: python -m pipeline.batch.prepare --input [DATA_DIR] --output pipeline/data/batch_input.jsonl
2. Process: python -m pipeline.batch.process --input pipeline/data/batch_input.jsonl --output pipeline/data/batch_output.jsonl
3. Import: python -m pipeline.batch.import_results --input pipeline/data/batch_output.jsonl

각 단계 완료 후 결과를 확인하고 다음 단계를 진행하세요.

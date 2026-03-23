---
name: ml-sandbox
description: ml-sandbox GPU 실행 파이프라인 (코드 실행, figure 생성, 결과 회수)
allowed-tools: Bash(ssh *), Bash(rsync *), Bash(python *), Bash(git *), Read
---
ml-sandbox GPU execution pipeline:

0. GPU 패스스루 확인:
   ssh hj-remote "lxc config device show ml-sandbox"

1. content.json pre-execution 상태 복원:
   git restore pipeline/data/ml_written/*/content.json

2. 스크립트 동기화:
   rsync -avz --delete pipeline/generators/ml_outputs.py ml-sandbox:/workspace/pipeline/generators/

3. 패키지 설치 (필요 시):
   ssh ml-sandbox "pip3 install gensim konlpy torch --index-url https://download.pytorch.org/whl/cu121"

4. GPU 검증:
   ssh ml-sandbox "python3 -c 'import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))'"

5. 실행:
   - 단일: ssh ml-sandbox "cd /workspace && python3 -m pipeline.generators.ml_outputs --slug [slug] --execute"
   - 전체: ssh ml-sandbox "cd /workspace && python3 -m pipeline.generators.ml_outputs --all --execute"

6. 시각 검증: Claude Code가 Read 도구로 PNG 직접 확인
   Read /path/to/backend/media/figures/outputs/[slug]/[slug]_fig_1.png

7. 결과 회수:
   rsync -avz ml-sandbox:/workspace/pipeline/data/ml_written/ pipeline/data/ml_written/
   rsync -avz ml-sandbox:/workspace/backend/media/figures/outputs/ backend/media/figures/outputs/

8. 커밋 → push → import --update

GPU 모델 실행 기준 (RTX 3090 24GB):
- sklearn, numpy, pandas → CPU
- gensim Word2Vec, fastText → CPU ~200MB
- BERT-base, RoBERTa, DistilBERT, GPT-2, T5 → ~1.5-3GB ✅
- LLaMA 7B, Mistral 7B → ~14GB fp16 ✅
- LLaMA 13B → int8 ~13GB ✅
- LLaMA 30B → int4 ~15GB ✅
- LLaMA 65B+ → ❌ API 호출로 대체

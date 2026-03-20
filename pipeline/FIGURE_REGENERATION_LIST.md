# Figure 재생성 목록

생성일: 2026-03-20

## 미생성 (6개)
figure가 아예 없는 항목들. 우선 생성 필요.

| # | Slug | 원인 |
|---|------|------|
| 1 | albert | SVG→PNG 변환 실패 (sanitize 불가) |
| 2 | edm | SVG→PNG 변환 실패 (sanitize 불가) |
| 3 | kimi-k2-5 | SVG→PNG 변환 실패 (sanitize 불가) |
| 4 | retnet | SVG→PNG 변환 실패 (sanitize 불가) |
| 5 | deepseek-r1-zero | SVG→PNG 변환 실패 (sanitize 불가) |
| 6 | flow-matching | SVG→PNG 변환 실패 (sanitize 불가) |

## 텍스트 잘림/Clipping (13개)
제목이나 라벨이 박스 경계에서 잘리는 문제.

| # | Slug | 문제 상세 |
|---|------|----------|
| 1 | claude-4 | "x N Layers (undisclosed)" 텍스트 overflow |
| 2 | claude-4-5 | "Embed dim (Undisclosed)", "x N/2 Layers" 왼쪽 경계 밖 clipping |
| 3 | cohere-command-a | "SwiGLU Network" 우측 잘림, "Vocab size" overflow |
| 4 | falcon | "d_model = 14848" overflow, MQA 제목 잘림 |
| 5 | gated-deltanet | "Expanded DeltaNet Block" 제목 잘림 |
| 6 | gpt-4o | Cross-Modal 섹션 라벨 잘림 |
| 7 | llama-2 | GQA 제목 "Grou..." 잘림 |
| 8 | mamba-2 | Expanded 섹션 제목 잘림/겹침 |
| 9 | o3-pro | "Heads: N (undisclos..." 잘림 |
| 10 | olmo | 제목 파라미터 수 잘림, SwiGLU FFN 상단 경계 밖 |
| 11 | roberta | MHA Expanded 제목 "Mult..." 잘림 |
| 12 | rwkv | "Time-...anded View" 제목 clipping |
| 13 | rwkv-7 | "RWKV-7 '...ta Rule" 제목 clipping |

## 텍스트 Overflow / 경계 초과 (4개)
요소가 다이어그램 경계 밖으로 삐져나감.

| # | Slug | 문제 상세 |
|---|------|----------|
| 1 | deberta | 왼쪽 dimension 주석 영역 밖으로 삐져나감, 폰트 매우 작음 |
| 2 | grok-3 | "Output Probabilities" 경계 넘어 겹침, annotation 삐져나감 |
| 3 | minicpm-v | 점선 연결 삐져나감, 텍스트 작고 밀집 |
| 4 | operator | Agent Core 박스가 헤더 영역과 겹침 |

## 가독성 부족 (5개)
텍스트가 너무 작거나 밀집되어 읽기 어려움.

| # | Slug | 문제 상세 |
|---|------|----------|
| 1 | hunyuanvideo | 전체 텍스트 매우 작고 밀집, 라벨 겹침 |
| 2 | internvl | Pixel Shuffle Detail 텍스트 너무 작음 |
| 3 | kling-3 | Attention 섹션 텍스트 너무 작음 |
| 4 | manus | 전체 텍스트 매우 작아 가독성 불량 |
| 5 | mcp | 하단 영역 텍스트 매우 작음 |

## 렌더링 결함 (2개)

| # | Slug | 문제 상세 |
|---|------|----------|
| 1 | h3 | Multiplicative Gate 라벨 겹침 |
| 2 | toolformer | Inference 섹션 검은 영역이 내부 요소를 가림 |

---

## 재생성 방법

```bash
cd /Users/dorae222/Documents/Obsidian/blog-jun/pipeline

# 특정 slug만 재생성
ANTHROPIC_API_KEY='...' DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib \
  python batch_generate_figures.py all --force \
  --slug albert,edm,kimi-k2-5,retnet,deepseek-r1-zero,flow-matching

# 품질 이슈 있는 것들 재생성
ANTHROPIC_API_KEY='...' DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib \
  python batch_generate_figures.py all --force \
  --slug claude-4,claude-4-5,cohere-command-a,falcon,gated-deltanet,gpt-4o,llama-2,mamba-2,o3-pro,olmo,roberta,rwkv,rwkv-7,deberta,grok-3,minicpm-v,operator,hunyuanvideo,internvl,kling-3,manus,mcp,h3,toolformer
```

## 총계
- 미생성: 6개
- 품질 이슈: 24개
- **합계: 30개** (전체 182개 중 16.5%)

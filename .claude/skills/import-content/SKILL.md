---
name: import-content
description: pipeline/data/에서 Django DB로 컨텐츠 임포트
allowed-tools: Bash(python *), Bash(ssh *), Read
---
컨텐츠 타입별 임포트 스크립트:

| 대상 | 커맨드 |
|------|--------|
| Papers | `python pipeline/import_papers_written.py [--dry-run] [--update]` |
| Architectures | `python pipeline/import_architectures.py [--dry-run] [--update]` |
| ML | `python pipeline/import_ml_written.py [--dry-run] [--update] [--reset]` |
| Data | `python pipeline/import_data_written.py [--dry-run] [--update]` |
| Colab | `python pipeline/import_colab_written.py [--dry-run] [--update]` |

옵션:
- `--dry-run`: 변경 없이 미리보기
- `--update`: 기존 포스트 content + tags 업데이트
- `--reset` (ML만): 기존 포스트 삭제 후 재생성

항상 `--dry-run` 먼저 실행하고 결과를 보여주세요.
import 후 서버 반영 시 deploy 스킬 사용.

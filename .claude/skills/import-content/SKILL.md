---
name: import-content
description: pipeline/data/에서 Django DB로 컨텐츠 임포트
allowed-tools: Bash(python *), Bash(ssh *), Read
---
컨텐츠 타입별 임포트:
- ML: python manage.py import_ml_written --data-dir pipeline/data/ml_written/
- Cloud: python manage.py import_cloud_content --data-dir content/cloud/
- Architecture: python pipeline/importers/architectures.py --data-dir pipeline/data/architectures_written/
- Papers: python pipeline/importers/papers.py --data-dir pipeline/data/papers_written/
- Colab: python pipeline/importers/colab.py --data-dir pipeline/data/colab_written/

항상 --dry-run 먼저 실행하고 결과를 보여주세요.

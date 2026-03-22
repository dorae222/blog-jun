---
name: content-pipeline
description: 컨텐츠 파이프라인 실행 — 스캔, 전처리, 배치 생성, 임포트
tools: Read, Grep, Glob, Bash
model: sonnet
maxTurns: 25
---
blog-jun 컨텐츠 파이프라인을 관리합니다.

작업 흐름:
1. pipeline/data/ 디렉토리 스캔 — 새 컨텐츠 확인
2. 전처리 필요 시 preprocessor 실행
3. Batch API로 컨텐츠 보강/생성
4. 결과 임포트 (Django management command)
5. 커버 이미지 생성
6. 품질 검사

프로젝트 구조:
- pipeline/utils/ — 공통 유틸리티
- pipeline/importers/ — 컨텐츠 임포트
- pipeline/generators/ — 이미지/컨텐츠 생성
- pipeline/batch/ — OpenAI Batch API
- pipeline/preprocessing/ — 전처리

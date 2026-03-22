# 리팩토링 교훈

## 한글 폰트 (cairosvg)
- `fonts-noto-cjk` 설치만으로 부족. fontconfig 별칭 설정으로 KR 변형을 명시적으로 우선 지정해야 함
- Docker multi-stage build에서 폰트는 production stage에 설치 (builder 아님)
- `fc-list :lang=ko` 으로 실제 등록된 폰트 이름 확인 필수

## Pipeline 구조
- 52개 스크립트가 flat하게 있으면 관리 불가 → 6개 패키지로 분리
- management commands는 `sys.path`로 pipeline을 import하므로, 루트 레벨 파일 유지 필요
- deprecated 스크립트는 git history에 있으므로 과감하게 삭제

## Backend
- serializer에서 반복되는 URL 빌딩 로직 → mixin으로 추출
- PostManager.published() 등 자주 쓰는 필터는 커스텀 매니저로

## 카테고리 재구조화
- 기존 aws → 10개 도메인 분할 시, 기존 카테고리의 포스트를 안전하게 이동하는 로직 필요
- TAG_TO_SUBCATEGORY 맵은 태그 추가될 때마다 유지보수 필요

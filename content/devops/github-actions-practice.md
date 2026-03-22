---
title: "GitHub Actions 실전 가이드: 워크플로우부터 배포까지"
slug: "github-actions-practice"
category: cloud
tags: ["devops", "github-actions", "cicd", "automation"]
status: published
post_type: article
quality_score: 9.0
created_at: "2026-03-22T00:00:00+09:00"
---

# GitHub Actions 실전 가이드: 워크플로우부터 배포까지

## 1. GitHub Actions 기본 개념

GitHub Actions는 GitHub에 내장된 **CI/CD 및 자동화 플랫폼**이다. 리포지토리에서 발생하는 이벤트를 기반으로 워크플로우를 자동 실행할 수 있다.

### 핵심 구성 요소

```
┌─────────────────────────────────────────────────────┐
│                   Workflow                           │
│  (.github/workflows/ci.yml)                         │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │              Job: build                      │    │
│  │  runs-on: ubuntu-latest                      │    │
│  │                                              │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐    │    │
│  │  │  Step 1  │→│  Step 2  │→│  Step 3  │    │    │
│  │  │ Checkout │ │  Build   │ │  Test    │    │    │
│  │  └──────────┘ └──────────┘ └──────────┘    │    │
│  └─────────────────────────────────────────────┘    │
│                      │ depends on                    │
│                      ▼                               │
│  ┌─────────────────────────────────────────────┐    │
│  │              Job: deploy                     │    │
│  │  runs-on: ubuntu-latest                      │    │
│  │  needs: build                                │    │
│  │                                              │    │
│  │  ┌──────────┐ ┌──────────┐                  │    │
│  │  │  Step 1  │→│  Step 2  │                  │    │
│  │  │  Login   │ │  Deploy  │                  │    │
│  │  └──────────┘ └──────────┘                  │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

| 구성 요소 | 설명 |
|-----------|------|
| **Workflow** | 자동화된 전체 프로세스. YAML 파일로 정의 |
| **Job** | 워크플로우 내의 작업 단위. 같은 러너에서 실행 |
| **Step** | Job 내의 개별 단계. 순차적으로 실행 |
| **Action** | 재사용 가능한 단위 작업 (Marketplace에서 공유) |
| **Runner** | 워크플로우를 실행하는 서버 환경 |

---

## 2. 워크플로우 YAML 구조 상세

워크플로우 파일은 `.github/workflows/` 디렉토리에 위치하며, YAML 형식으로 작성한다.

```yaml
# .github/workflows/ci.yml

name: CI Pipeline                  # 워크플로우 이름

on:                                # 트리거 조건
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:                               # 워크플로우 전역 환경변수
  NODE_VERSION: '20'
  REGISTRY: ghcr.io

permissions:                       # GITHUB_TOKEN 권한 설정
  contents: read
  packages: write

jobs:                              # 작업 정의
  lint:                            # Job ID
    name: Code Lint                # 표시 이름
    runs-on: ubuntu-latest         # 러너 환경
    timeout-minutes: 10            # 타임아웃 설정

    steps:
      - name: Checkout code        # Step 이름
        uses: actions/checkout@v4  # 외부 Action 사용

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:                      # Action에 전달할 파라미터
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci                # 쉘 명령어 실행

      - name: Run linter
        run: npm run lint

  test:
    name: Run Tests
    runs-on: ubuntu-latest
    needs: lint                    # lint Job 완료 후 실행

    strategy:
      matrix:                      # 매트릭스 빌드
        node-version: [18, 20, 22]

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm test
```

### 주요 문법 요소

```yaml
# 조건부 실행
- name: Deploy to production
  if: github.ref == 'refs/heads/main' && github.event_name == 'push'
  run: ./deploy.sh

# 환경변수 참조
- name: Use context
  run: |
    echo "Branch: ${{ github.ref_name }}"
    echo "SHA: ${{ github.sha }}"
    echo "Actor: ${{ github.actor }}"

# Job 출력 전달
jobs:
  build:
    outputs:
      version: ${{ steps.version.outputs.value }}
    steps:
      - id: version
        run: echo "value=1.2.3" >> $GITHUB_OUTPUT

  deploy:
    needs: build
    steps:
      - run: echo "Deploying version ${{ needs.build.outputs.version }}"
```

---

## 3. 트리거 종류

GitHub Actions는 다양한 이벤트로 워크플로우를 트리거할 수 있다.

### 주요 트리거 유형

```yaml
on:
  # 1. Push 이벤트
  push:
    branches: [main, 'release/**']
    tags: ['v*']
    paths:
      - 'src/**'
      - '!src/**/*.test.js'      # 특정 경로 제외

  # 2. Pull Request 이벤트
  pull_request:
    types: [opened, synchronize, reopened]
    branches: [main]

  # 3. 스케줄 (Cron)
  schedule:
    - cron: '0 9 * * 1'          # 매주 월요일 09:00 UTC

  # 4. 수동 트리거
  workflow_dispatch:
    inputs:
      environment:
        description: '배포 환경'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production
      dry_run:
        description: 'Dry run 모드'
        required: false
        type: boolean
        default: false

  # 5. 다른 워크플로우에서 호출
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
    secrets:
      deploy_key:
        required: true

  # 6. 이슈/PR 코멘트
  issue_comment:
    types: [created]
```

### 트리거 필터링 팁

```yaml
# 특정 파일 변경 시에만 실행
on:
  push:
    paths:
      - 'backend/**'     # backend 디렉토리 변경 시만
      - 'Dockerfile'
    paths-ignore:
      - '**.md'           # 마크다운 변경은 무시
      - 'docs/**'
```

---

## 4. 러너 환경

### GitHub-Hosted 러너

| 러너 | OS | 특징 |
|------|-----|------|
| `ubuntu-latest` | Ubuntu 22.04 | 가장 범용적, Linux 환경 |
| `ubuntu-24.04` | Ubuntu 24.04 | 최신 Ubuntu |
| `windows-latest` | Windows Server 2022 | .NET, PowerShell |
| `macos-latest` | macOS 14 (Sonoma) | iOS/macOS 빌드 |

### Self-Hosted 러너

내부 인프라에서 러너를 직접 운영할 수 있다:

```yaml
jobs:
  build:
    runs-on: [self-hosted, linux, x64]   # 라벨 기반 선택
    steps:
      - uses: actions/checkout@v4
      - run: ./build.sh
```

Self-Hosted 러너의 장점:
- 커스텀 하드웨어(GPU 등) 사용 가능
- 내부 네트워크 리소스 접근 가능
- 실행 시간 제한 없음
- 비용 절감 (대규모 사용 시)

---

## 5. 시크릿 관리

### Repository Secrets

```yaml
# 시크릿은 ${{ secrets.NAME }} 으로 참조
steps:
  - name: Login to Registry
    run: |
      echo "${{ secrets.REGISTRY_PASSWORD }}" | \
        docker login ${{ vars.REGISTRY_URL }} \
          -u ${{ secrets.REGISTRY_USERNAME }} --password-stdin
```

### Environment Secrets

환경별로 시크릿을 분리 관리할 수 있다:

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production        # 환경 지정
    steps:
      - name: Deploy
        run: ./deploy.sh
        env:
          DB_HOST: ${{ secrets.DB_HOST }}         # production 환경 시크릿
          API_KEY: ${{ secrets.API_KEY }}
```

### 시크릿 관리 베스트 프랙티스

1. **최소 권한 원칙**: 각 워크플로우에 필요한 시크릿만 노출
2. **환경 분리**: staging과 production 시크릿을 별도 관리
3. **보호 규칙**: production 환경에 승인자(reviewer) 설정
4. **정기 로테이션**: 시크릿을 주기적으로 갱신
5. **로그 마스킹**: GitHub가 자동으로 시크릿 값을 `***`로 마스킹

---

## 6. 매트릭스 빌드

여러 환경 조합을 병렬로 테스트할 수 있다:

```yaml
jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false             # 하나 실패해도 나머지 계속 실행
      max-parallel: 4              # 최대 병렬 수
      matrix:
        os: [ubuntu-latest, macos-latest]
        node-version: [18, 20, 22]
        include:                   # 추가 조합
          - os: ubuntu-latest
            node-version: 22
            experimental: true
        exclude:                   # 제외 조합
          - os: macos-latest
            node-version: 18

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
      - run: npm ci
      - run: npm test
        continue-on-error: ${{ matrix.experimental || false }}
```

위 설정은 다음 조합을 생성한다:

```
ubuntu-latest + Node 18  ✓
ubuntu-latest + Node 20  ✓
ubuntu-latest + Node 22  ✓ (experimental)
macos-latest  + Node 20  ✓
macos-latest  + Node 22  ✓
```

---

## 7. 캐싱 전략

빌드 시간을 크게 단축할 수 있는 캐싱 설정:

```yaml
# 방법 1: setup-node 내장 캐시 (간편)
- uses: actions/setup-node@v4
  with:
    node-version: 20
    cache: 'npm'

# 방법 2: actions/cache 직접 사용 (세밀한 제어)
- name: Cache node_modules
  uses: actions/cache@v4
  id: npm-cache
  with:
    path: node_modules
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-

- name: Install dependencies
  if: steps.npm-cache.outputs.cache-hit != 'true'
  run: npm ci
```

### Docker 레이어 캐싱

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build and push
  uses: docker/build-push-action@v6
  with:
    context: .
    push: true
    tags: ${{ vars.REGISTRY_URL }}/${{ vars.IMAGE_NAME }}:latest
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

---

## 8. 아티팩트 업로드/다운로드

Job 간에 빌드 결과물을 공유할 수 있다:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/
          retention-days: 7        # 보관 기간

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Download build artifact
        uses: actions/download-artifact@v4
        with:
          name: build-output
          path: dist/

      - name: Deploy
        run: |
          ls -la dist/
          # 배포 로직
```

---

## 9. 실전 예시: Node.js + Docker 빌드 → 테스트 → 배포

전체 CI/CD 파이프라인 예시:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

permissions:
  contents: read
  packages: write

jobs:
  # ──────────────── 테스트 ────────────────
  test:
    name: Test
    runs-on: ubuntu-latest

    services:                      # 서비스 컨테이너
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: testuser
          POSTGRES_PASSWORD: testpass
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - run: npm ci
      - run: npm run lint
      - run: npm test
        env:
          DATABASE_URL: postgresql://testuser:testpass@localhost:5432/testdb

      - name: Upload coverage
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: coverage/

  # ──────────────── 빌드 & 푸시 ────────────────
  build:
    name: Build & Push Image
    runs-on: ubuntu-latest
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    outputs:
      image_tag: ${{ steps.meta.outputs.tags }}

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=
            type=raw,value=latest

      - name: Build and push
        uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  # ──────────────── 배포 ────────────────
  deploy:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: build
    environment: production

    steps:
      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/app
            docker compose pull
            docker compose up -d
            docker image prune -f

      - name: Health check
        run: |
          for i in $(seq 1 30); do
            if curl -sf "${{ secrets.HEALTH_CHECK_URL }}" > /dev/null; then
              echo "Health check passed!"
              exit 0
            fi
            sleep 5
          done
          echo "Health check failed!"
          exit 1

      - name: Notify on success
        if: success()
        run: |
          curl -X POST "${{ secrets.WEBHOOK_URL }}" \
            -H 'Content-Type: application/json' \
            -d '{"text": "Deployment successful: ${{ github.sha }}"}'

      - name: Notify on failure
        if: failure()
        run: |
          curl -X POST "${{ secrets.WEBHOOK_URL }}" \
            -H 'Content-Type: application/json' \
            -d '{"text": "Deployment FAILED: ${{ github.sha }}"}'
```

---

## 10. 재사용 가능한 워크플로우

### 호출 가능한 워크플로우 정의

```yaml
# .github/workflows/reusable-deploy.yml
name: Reusable Deploy

on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
      image_tag:
        required: true
        type: string
    secrets:
      server_host:
        required: true
      ssh_key:
        required: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - name: Deploy
        run: |
          echo "Deploying ${{ inputs.image_tag }} to ${{ inputs.environment }}"
```

### 호출하는 워크플로우

```yaml
# .github/workflows/main.yml
name: Main Pipeline

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      tag: ${{ steps.tag.outputs.value }}
    steps:
      - id: tag
        run: echo "value=${{ github.sha }}" >> $GITHUB_OUTPUT

  deploy-staging:
    needs: build
    uses: ./.github/workflows/reusable-deploy.yml
    with:
      environment: staging
      image_tag: ${{ needs.build.outputs.tag }}
    secrets:
      server_host: ${{ secrets.STAGING_HOST }}
      ssh_key: ${{ secrets.STAGING_SSH_KEY }}

  deploy-production:
    needs: [build, deploy-staging]
    uses: ./.github/workflows/reusable-deploy.yml
    with:
      environment: production
      image_tag: ${{ needs.build.outputs.tag }}
    secrets:
      server_host: ${{ secrets.PROD_HOST }}
      ssh_key: ${{ secrets.PROD_SSH_KEY }}
```

### 복합 액션 (Composite Action)

자주 사용하는 단계를 묶어 재사용할 수 있다:

```yaml
# .github/actions/setup-project/action.yml
name: 'Setup Project'
description: '프로젝트 환경 설정'

inputs:
  node-version:
    description: 'Node.js version'
    required: false
    default: '20'

runs:
  using: 'composite'
  steps:
    - uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
        cache: 'npm'

    - name: Install dependencies
      shell: bash
      run: npm ci

    - name: Verify setup
      shell: bash
      run: node --version && npm --version
```

사용:

```yaml
steps:
  - uses: actions/checkout@v4
  - uses: ./.github/actions/setup-project
    with:
      node-version: '22'
  - run: npm test
```

---

## 마무리

GitHub Actions는 GitHub 생태계에 긴밀하게 통합된 강력한 CI/CD 플랫폼이다. 핵심 포인트를 정리하면:

- **워크플로우는 YAML로 선언적으로 정의**하며, 다양한 이벤트로 트리거할 수 있다
- **매트릭스 빌드**로 여러 환경을 병렬 테스트하고, **캐싱**으로 빌드 시간을 단축한다
- **시크릿은 환경별로 분리 관리**하고, 최소 권한 원칙을 따른다
- **재사용 가능한 워크플로우**로 DRY 원칙을 지키며 유지보수성을 높인다
- **서비스 컨테이너**를 활용하면 DB 등 의존성이 있는 통합 테스트도 쉽게 구성할 수 있다

다음 글에서는 배포 전략(Rolling, Blue-Green, Canary)의 비교와 실전 적용 방법을 다룰 예정이다.

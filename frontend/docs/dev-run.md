# 로컬 개발 서버 실행 (프론트엔드)

모든 명령은 aiops-build 서버의 `~/projects/blog-jun-prod-src/frontend`에서. 개발 서버는 **127.0.0.1에만** 붙는다.

## 모드

| 명령 | 주소 | 백엔드 |
|---|---|---|
| `npm run dev:workspace` | http://127.0.0.1:5180 | 로컬 blog-api(127.0.0.1:18000, H1 `~/projects/blog-api/dev/up.sh`)로 `/api`·`/media` 프록시 |
| `npm run dev:mock` | http://127.0.0.1:5180 | 백엔드 없이 `dev/mock-api.js`(메모리 저장, 재시작 시 초기화) |
| `npm run dev` | :3000 | 예전 그대로(`VITE_PROXY_TARGET` 또는 localhost:8000) |

운영 빌드(`npm run build`, Dockerfile)는 mode=production이라 위 분기와 mock 코드를 전혀 쓰지 않는다.

## 띄우기 / 내리기 (백그라운드)

```bash
cd ~/projects/blog-jun-prod-src/frontend
npm ci                                   # 처음 한 번
mkdir -p ~/.cache/blog-workspace
nohup npm run dev:workspace > ~/.cache/blog-workspace/vite-dev.log 2>&1 < /dev/null &
echo $! > ~/.cache/blog-workspace/vite-dev.pid
tail -f ~/.cache/blog-workspace/vite-dev.log

# 내리기
pkill -f "vite --mode workspace"         # mock이면 "vite --mode mock"
```

## 브라우저로 쓰기 (맥에서)

```bash
ssh -N -L 5180:127.0.0.1:5180 aiops-build
# → http://localhost:5180
```

- workspace 모드 로그인: `~/projects/blog-api/dev/seed.env`의 `SEED_ADMIN_USERNAME`/`SEED_ADMIN_PASSWORD`(staff),
  `SEED_READER_*`(일반 사용자 — 메모·편집기 가드 확인용).
- mock 모드 로그인: `hj`(staff) / `guest`(일반), 비밀번호 아무거나. 챗에 "에러"→503, "제한"→429, "바빠"→busy 이벤트, "느리게"→느린 스트림.

## 확인 포인트

- 단축키: `n` 새 글, `m` 빠른 메모(입력 중·모달 열림 중엔 무시). 에디터: Cmd/Ctrl+S 저장, Alt+P 미리보기, Cmd/Ctrl+K 글 링크.
- `/notes`(staff만), 대시보드 상단 "이어 쓰기"/"최근 메모".
- 챗봇 버튼(좌하단)은 공개 화면에서만 보임(에디터·대시보드·메모·로그인 화면에선 숨김).
- Turnstile: `VITE_TURNSTILE_SITEKEY`가 있으면 챗 패널에 위젯이 뜨고 토큰을 `X-Turnstile-Token` 헤더로 보낸다. 없으면 표시 안 함.

## 테스트

```bash
npm test        # node 내장 테스트 러너(새 의존성 없음): SSE 파서, #태그 파싱, slug, timeAgo 등
npm run lint    # 오류 0 (경고는 기존 설정상 JSX 사용 변수를 못 알아봐서 많음)
npm run build
```

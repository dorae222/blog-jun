# 화면 캡처 / 라이브 페이지 검증 규칙

## SPA(blog-jun frontend) 캡처 시 주의사항

blog.dorae222.com은 React SPA이므로 HTML response는 빈 shell이고, JavaScript 실행 후에야 컨텐츠가 렌더링된다. headless 브라우저로 캡처할 때 **반드시 렌더링 완료를 기다려야** 한다.

### Chrome headless 권장 옵션

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless \
  --disable-gpu \
  --virtual-time-budget=15000 \
  --hide-scrollbars \
  --window-size=1400,1200 \
  --screenshot=/path/to/output.png \
  https://blog.dorae222.com/post/SLUG
```

핵심:
- `--virtual-time-budget=15000` - 15초 가상 시간 (네트워크/렌더링 완료 대기)
- 일부 페이지는 더 긴 시간 필요 (ArchitectureTreePage 같은 D3 렌더 페이지)

### 캡처 후 검증

캡처가 제대로 됐는지 확인하려면:

1. **파일 크기 확인**: 빈 페이지(스켈레톤)는 보통 < 30KB. 정상 캡처는 80KB+
2. **시각적 검증**: Read 도구로 PNG 직접 확인
3. 빈 화면이면 다음 옵션 시도:
   - `--virtual-time-budget` 값 늘림 (30000ms)
   - `sleep 5` 추가 후 재시도
   - Chrome에서 직접 확인

### 대안: API + 컨텐츠 직접 검증

캡처가 어려운 경우, API 응답으로 컨텐츠 검증:

```bash
curl -s "https://blog.dorae222.com/api/posts/SLUG/" | python3 -c "
import json, sys
d = json.load(sys.stdin)
content = d.get('content', '')
# 특정 패턴/문자열 확인
print('len:', len(content))
print('has X:', 'X' in content)
"
```

### 절대 하지 말 것

- 짧은 timeout (5초 미만) - SPA는 가상 시간 10초 이상 권장
- 첫 캡처가 빈 페이지인데 그대로 사용자에게 보고 - 반드시 재시도
- `screencapture` (macOS 명령어) 무인 자동화 - GUI 의존, 검증 어려움

## API 호출 시 Rate Limit 주의

DRF throttle이 활성화되어 있어 짧은 시간에 많은 API 호출 시 차단된다.

- 점검 / 수정 작업은 ORM 직접 사용 (Django shell + Post.objects)
- API curl 호출은 검증 단계에서만, 최소 횟수로
- 차단 발생 시: `docker compose exec redis redis-cli FLUSHALL` 로 throttle 캐시 정리

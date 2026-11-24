/**
 * 홈에 시리즈를 늘어놓는 순서.
 *
 * 편수 내림차순으로 고정해 두니 매번 같은 열 개만 보였다. 뒤에 있는 시리즈는
 * 사실상 노출되지 않는다. 그렇다고 완전 무작위로 돌리면 방금 쓴 글이 묻힌다.
 *
 * 그래서 **최신도로 점수를 주고 그 점수에 흔들림을 섞는다**. 최근에 글이 붙은
 * 시리즈는 앞쪽에 머물 확률이 높고, 오래된 시리즈도 가끔 앞으로 올라온다.
 * 방문할 때마다 배열이 달라지되 완전히 뒤집히지는 않는다.
 */

const DAY = 24 * 60 * 60 * 1000
const HALF_LIFE_DAYS = 45      // 이 기간이 지날 때마다 최신도 점수가 절반이 된다
const JITTER = 0.55            // 흔들림 폭. 0이면 순수 최신순, 1에 가까울수록 무작위에 가깝다

function freshness(iso, now) {
  if (!iso) return 0
  const t = Date.parse(iso)
  if (Number.isNaN(t)) return 0
  const days = Math.max(0, (now - t) / DAY)
  return Math.pow(0.5, days / HALF_LIFE_DAYS)
}

/**
 * 편수는 "볼 만한 시리즈인가"의 대리 지표라 완전히 버리지는 않는다.
 * 다만 로그를 씌워 10편과 30편의 차이가 3배가 아니라 1.4배쯤 되게 눌러 둔다.
 */
function volume(count) {
  return Math.log2(1 + Math.max(0, count || 0)) / 6
}

export function rankSeries(list, seed = Math.random()) {
  const now = Date.now()
  // 같은 방문 안에서는 탭을 옮겨도 순서가 유지되도록 시드를 하나만 쓴다.
  let s = Math.floor(seed * 2 ** 31) || 1
  const rand = () => {
    s = (s * 1103515245 + 12345) & 0x7fffffff
    return s / 0x7fffffff
  }

  return list
    .map((it) => {
      const base = freshness(it.last_post_at, now) + volume(it.post_count)
      return { it, score: base * (1 - JITTER + JITTER * 2 * rand()) }
    })
    .sort((a, b) => b.score - a.score)
    .map((x) => x.it)
}

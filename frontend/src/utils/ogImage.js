/**
 * OG(링크 미리보기) 이미지 주소를 만든다.
 *
 * 왜 표지와 OG 이미지를 갈라 놓나:
 * 표지는 움직이는 SVG인데, 슬랙·카카오톡·디스코드의 링크 미리보기 크롤러는 SVG를
 * 대개 그리지 않는다(그리는 곳도 애니메이션은 안 돈다). 그래서 카드에 보이는 그림은
 * SVG, 링크를 붙였을 때 나오는 그림은 배포된 PNG로 나눈다.
 *
 * 갈라 놓을 수 있는 근거:
 * 표지를 SVG로 바꾸면서 PNG 파일을 지우지 않았고, SVG 키를 **PNG와 같은 이름에
 * 확장자만 바꾼 꼴**로 올렸다(pipeline/apply_studio_covers.py의 motion_key).
 *     /media/posts/covers/xgboost-lightgbm-v3.svg
 *  -> /media/posts/covers/xgboost-lightgbm-v3.png
 *     /media/series/covers/a2a-protocol-emblem2.svg
 *  -> /media/series/covers/a2a-protocol-emblem2.png
 *
 * -v3 / -emblem2 는 배포된 PNG의 이름표다. 그 표시가 없는 표지(-m1.svg)는 원래
 * PNG가 없던 글이라 SVG를 그대로 돌려준다. 없는 PNG를 가리키는 것보다 낫다.
 */
const PNG_BACKED = /(-v3|-emblem2)\.svg$/i

const SITE_ORIGIN = 'https://blog.dorae222.com'

/** 표지 URL -> OG용 이미지 URL(절대 주소). 크롤러는 상대 경로를 못 따라간다. */
export function ogImageUrl(coverUrl) {
  if (!coverUrl) return null
  const path = PNG_BACKED.test(coverUrl)
    ? coverUrl.replace(/\.svg$/i, '.png')
    : coverUrl
  if (/^https?:\/\//i.test(path)) return path
  return `${SITE_ORIGIN}${path.startsWith('/') ? '' : '/'}${path}`
}

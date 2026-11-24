"""시리얼라이저 믹스인 - cover_image_url 등 공통 필드 빌더."""


class ImageUrlMixin:
    """cover_image_url, figure_url 시리얼라이저 공통 빌더."""

    def _build_url(self, file_field):
        """미디어 URL은 상대 경로로 준다.

        절대 URL을 만들면 Cloudflare 터널→ingress 구간에서 X-Forwarded-Proto가
        유실될 때 http:// 로 나가고, https 페이지에서 mixed content로 차단돼
        이미지가 통째로 안 보인다. 상대 경로는 프로토콜·도메인에 영향받지 않는다.
        """
        if not file_field:
            return None
        return file_field.url

    def get_cover_image_url(self, obj):
        if obj.cover_image:
            return self._build_url(obj.cover_image)
        # fallback: ArchitectureEntry figure
        try:
            entry = obj.architecture_entries.first()
            if entry and entry.figure:
                return self._build_url(entry.figure)
        except Exception:
            pass
        return None

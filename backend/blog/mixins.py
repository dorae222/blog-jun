"""시리얼라이저 믹스인 — cover_image_url 등 공통 필드 빌더."""


class ImageUrlMixin:
    """cover_image_url, figure_url 시리얼라이저 공통 빌더."""

    def _build_url(self, file_field):
        if not file_field:
            return None
        request = self.context.get('request')
        url = file_field.url
        return request.build_absolute_uri(url) if request else url

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

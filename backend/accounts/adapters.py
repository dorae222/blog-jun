from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        """소셜 로그인 시 유저명을 provider_uid 조합으로 설정."""
        user = super().save_user(request, sociallogin, form)
        # 기본 유저명이 비어있으면 provider + uid 기반으로 설정
        if not user.username:
            provider = sociallogin.account.provider
            uid = sociallogin.account.uid
            user.username = f'{provider}_{uid}'
            user.save(update_fields=['username'])
        return user

from urllib.parse import urlencode

from django.conf import settings
from django.shortcuts import redirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    user = request.user
    data = {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_staff': user.is_staff,
    }

    # 소셜 계정 정보 추가 (avatar, provider)
    try:
        from allauth.socialaccount.models import SocialAccount
        social = SocialAccount.objects.filter(user=user).first()
        if social:
            data['provider'] = social.provider
            extra = social.extra_data
            if social.provider == 'github':
                data['avatar_url'] = extra.get('avatar_url', '')
                data['profile_url'] = extra.get('html_url', '')
                data['display_name'] = extra.get('name') or extra.get('login', '')
            elif social.provider == 'google':
                data['avatar_url'] = extra.get('picture', '')
                data['profile_url'] = ''
                data['display_name'] = extra.get('name', '')
    except Exception:
        pass

    return Response(data)


def social_login_callback(request):
    """allauth 소셜 로그인 완료 후 JWT 발급 및 프론트엔드 리다이렉트.

    allauth가 세션에 유저를 로그인시킨 후 이 뷰로 리다이렉트.
    JWT 토큰을 생성하여 프론트엔드 콜백 URL로 전달.
    """
    user = request.user
    if not user.is_authenticated:
        callback_url = settings.SOCIAL_LOGIN_CALLBACK_URL
        params = urlencode({'error': 'authentication_failed'})
        return redirect(f'{callback_url}?{params}')

    # JWT 토큰 생성
    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)

    callback_url = settings.SOCIAL_LOGIN_CALLBACK_URL
    params = urlencode({
        'access': access,
        'refresh': str(refresh),
    })
    return redirect(f'{callback_url}?{params}')

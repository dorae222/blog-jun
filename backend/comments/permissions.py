from rest_framework import permissions


class IsCommentAuthorOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # 삭제는 본인 또는 관리자
        if request.method == 'DELETE':
            return obj.author == request.user or request.user.is_staff
        # 수정은 본인만
        return obj.author == request.user

from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    message = "Se necesita una cuenta de administración."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_staff)

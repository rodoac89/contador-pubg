from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_200_OK,
    HTTP_201_CREATED,
)
from rest_framework.response import Response

from api.permissions import IsAdmin


def _registration_open():
    return not User.objects.filter(is_staff=True).exists()


def _session(user):
    token, _created = Token.objects.get_or_create(user=user)
    return {
        "token": token.key,
        "id": user.id,
        "username": user.username,
        "email": user.email,
    }


class SetupAPIView(APIView):
    """Dice si todavía se puede crear la primera cuenta de administración."""

    authentication_classes = []

    def get(self, request, *args, **kwargs):
        return Response({"registrationOpen": _registration_open()}, status=HTTP_200_OK)


class RegisterAPIView(APIView):
    """Crea la primera cuenta de administración y después queda cerrado."""

    authentication_classes = []

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")
        if not isinstance(username, str) or not isinstance(password, str):
            return Response(
                {"detail": "Usuario y contraseña son obligatorios."},
                status=HTTP_400_BAD_REQUEST,
            )
        username = username.strip()
        if not username or not password:
            return Response(
                {"detail": "Usuario y contraseña son obligatorios."},
                status=HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            if User.objects.select_for_update().filter(is_staff=True).exists():
                return Response(
                    {"detail": "El registro ya está cerrado."},
                    status=HTTP_403_FORBIDDEN,
                )
            user = User(username=username, is_staff=True, is_superuser=True)
            user.set_password(password)
            try:
                user.full_clean()
                validate_password(password, user)
            except ValidationError as exc:
                return Response(
                    {"detail": " ".join(exc.messages)},
                    status=HTTP_400_BAD_REQUEST,
                )
            user.save()
            Token.objects.create(user=user)

        return Response(_session(user), status=HTTP_201_CREATED)


class LoginAPIView(APIView):
    """Entrega un token de Django REST framework."""

    authentication_classes = []

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        if not isinstance(username, str) or not isinstance(password, str) or not username or not password:
            return Response(
                {"detail": "Usuario y contraseña son obligatorios."},
                status=HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(username=username).first()
        if user is None or not user.check_password(password):
            return Response(
                {"detail": "Usuario o contraseña incorrectos."},
                status=HTTP_401_UNAUTHORIZED,
            )
        if not user.is_staff:
            return Response(
                {"detail": "Esta cuenta no es de administración."},
                status=HTTP_403_FORBIDDEN,
            )
        return Response(_session(user), status=HTTP_200_OK)


class LogoutAPIView(APIView):
    permission_classes = [IsAdmin]

    def post(self, request, *args, **kwargs):
        Token.objects.filter(user=request.user).delete()
        logout(request)
        return Response({"detail": "Sesión cerrada."}, status=HTTP_200_OK)


class UserDataAPIView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request, *args, **kwargs):
        user = request.user
        return Response(
            {"id": user.id, "username": user.username, "email": user.email},
            status=HTTP_200_OK,
        )

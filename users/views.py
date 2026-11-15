import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.views import BAD_REQUEST, UNAUTHORIZED, invalid_data

from .serializers import RegisterSerializer, UserSerializer

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Авторизація"],
        summary="Реєстрація нового користувача",
        request=RegisterSerializer,
        responses={201: RegisterSerializer, 400: BAD_REQUEST},
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return invalid_data(serializer)
        user = serializer.save()
        logger.info("Зареєстровано користувача id=%s", user.id)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Авторизація"],
        summary="Дані поточного користувача",
        responses={200: UserSerializer, 401: UNAUTHORIZED},
    )
    def get(self, request):
        return Response(UserSerializer(request.user).data)

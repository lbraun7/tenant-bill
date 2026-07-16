from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.serializers import RegisterSerializer


class RegisterView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(request=RegisterSerializer, responses={201: RegisterSerializer})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        refresh = RefreshToken.for_user(result["user"])
        data = serializer.to_representation(result)
        data["tokens"] = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
        return Response(data, status=status.HTTP_201_CREATED)

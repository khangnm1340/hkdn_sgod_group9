from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, mixins, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    LogoutSerializer,
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


@extend_schema(
    tags=["Authentication"],
    summary="Đăng ký tài khoản mới",
    description="Tạo tài khoản người dùng mới với email, mật khẩu và họ tên.",
    request=RegisterSerializer,
    responses={
        201: OpenApiResponse(
            response=UserSerializer,
            description="Đăng ký tài khoản thành công",
        ),
        400: OpenApiResponse(description="Dữ liệu không hợp lệ hoặc email đã tồn tại"),
    },
)
class RegisterView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        response_data = UserSerializer(user).data
        response_data["message"] = "Đăng ký tài khoản thành công"
        return Response(response_data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Authentication"],
    summary="Đăng nhập hệ thống & Lấy JWT Token",
    description="Xác thực qua email & mật khẩu, trả về cặp JWT Token (access, refresh) và thông tin user.",
    responses={
        200: OpenApiResponse(description="Đăng nhập thành công, trả về cặp token và user info"),
        401: OpenApiResponse(description="Email hoặc mật khẩu không chính xác"),
    },
)
class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CustomTokenObtainPairSerializer


@extend_schema(
    tags=["Authentication"],
    summary="Làm mới Access Token",
    description="Nhận Refresh Token hợp lệ và trả về Access Token mới.",
)
class CustomTokenRefreshView(TokenRefreshView):
    pass


@extend_schema(
    tags=["Authentication"],
    summary="Đăng xuất & Vô hiệu hóa Refresh Token",
    description="Nhận Refresh Token và đưa vào danh sách đen (Blacklist).",
    request=LogoutSerializer,
    responses={
        200: OpenApiResponse(description="Đăng xuất thành công"),
        400: OpenApiResponse(description="Refresh token không hợp lệ hoặc thiếu"),
        401: OpenApiResponse(description="Chưa xác thực Bearer Token"),
    },
)
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = LogoutSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Đăng xuất thành công."}, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Authentication"],
    summary="Lấy hoặc cập nhật thông tin hồ sơ cá nhân",
    description="GET: Lấy thông tin tài khoản hiện tại. PATCH: Cập nhật họ và tên.",
    responses={
        200: UserSerializer,
        401: OpenApiResponse(description="Chưa xác thực Bearer Token"),
    },
)
class UserMeView(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, generics.GenericAPIView):
    http_method_names = ["get", "patch", "head", "options"]
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return UserUpdateSerializer
        return UserSerializer

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Authentication"],
    summary="Đổi mật khẩu tài khoản",
    description="Xác nhận mật khẩu cũ và cập nhật mật khẩu mới.",
    request=ChangePasswordSerializer,
    responses={
        200: OpenApiResponse(description="Đổi mật khẩu thành công"),
        400: OpenApiResponse(description="Mật khẩu cũ không chính xác hoặc mật khẩu mới không hợp lệ"),
        401: OpenApiResponse(description="Chưa xác thực Bearer Token"),
    },
)
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Đổi mật khẩu thành công."}, status=status.HTTP_200_OK
        )

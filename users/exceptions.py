from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    ValidationError,
)
from rest_framework.views import exception_handler

AUTH_MESSAGES = {
    "no_active_account": "Невірне ім'я користувача або пароль.",
    "token_not_valid": "Токен недійсний або строк його дії минув. Увійдіть знову.",
}


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response
    if isinstance(exc, ValidationError):
        response.data = {"detail": "Некоректні дані.", "errors": response.data}
    elif isinstance(exc, NotAuthenticated):
        response.data = {"detail": "Для цієї дії потрібно увійти в акаунт."}
    elif isinstance(exc, AuthenticationFailed):
        code = response.data.get("code") or getattr(exc.detail, "code", None)
        response.data = {
            "detail": AUTH_MESSAGES.get(str(code), "Не вдалося пройти автентифікацію.")
        }
    elif isinstance(exc, PermissionDenied):
        response.data = {"detail": str(exc.detail)}
    return response

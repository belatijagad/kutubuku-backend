from django.contrib.auth.hashers import check_password
from django.contrib.auth import get_user_model

class CustomBackend:

    def authenticate(self, request, username, password):
        CustomUser = get_user_model()
        try:
            user = CustomUser.objects.get(username=username)
            if user.check_password(password):
                return user
            else:
                return None
        except CustomUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        CustomUser = get_user_model()
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None
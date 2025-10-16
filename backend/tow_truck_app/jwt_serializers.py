"""
JWT сериализаторы для системы эвакуатора.

Кастомные сериализаторы для JWT токенов с дополнительными полями пользователя.
"""

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Кастомный сериализатор для JWT токенов с дополнительной информацией о пользователе.
    """
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Добавляем дополнительные поля в токен
        token['user_type'] = user.user_type
        token['username'] = user.username
        token['email'] = user.email
        token['phone'] = user.phone
        token['is_verified'] = user.is_verified
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Добавляем информацию о пользователе в ответ
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'phone': self.user.phone,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'user_type': self.user.user_type,
            'is_verified': self.user.is_verified,
            'avatar': self.user.avatar.url if self.user.avatar else None,
        }
        
        return data


class CustomTokenRefreshSerializer(TokenObtainPairSerializer):
    """
    Сериализатор для обновления JWT токенов.
    """
    
    def validate(self, attrs):
        refresh = self.token_class(attrs["refresh"])
        
        data = {"access": str(refresh.access_token)}
        
        if refresh.rotated:
            data["refresh"] = str(refresh)
        
        return data

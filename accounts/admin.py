from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from .forms import CustomUserChangeForm, CustomAdminUserCreationForm

class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {"fields": ("kakao_id", "nickname", "password",)}),
        ("Permissions", {"fields": ("is_active","is_staff","is_superuser","groups","user_permissions",)}),
        ("Important dates", {"fields": ("date_joined","last_login",)}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("kakao_id", "nickname","usable_password","password1","password2",),
        }),
    )
    form = CustomUserChangeForm
    add_form = CustomAdminUserCreationForm
    list_display = ("kakao_id","nickname","is_staff",)
    search_fields = ("kakao_id",)
    ordering = ("kakao_id",)

admin.site.register(User, CustomUserAdmin)

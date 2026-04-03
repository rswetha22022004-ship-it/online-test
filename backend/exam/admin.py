from django.contrib import admin

from .models import (
    Attempt,
    AttemptAnswer,
    Question,
    SMSNotification,
    Test,
    UserProfile,
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_filter = ("role",)


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("title", "created_by", "duration_minutes", "created_at")
    inlines = [QuestionInline]


class AttemptAnswerInline(admin.TabularInline):
    model = AttemptAnswer
    extra = 0


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "test", "score", "total", "submitted_at")
    inlines = [AttemptAnswerInline]


@admin.register(SMSNotification)
class SMSNotificationAdmin(admin.ModelAdmin):
    list_display = ("attempt", "status", "sent_by", "created_at")
    list_filter = ("status",)

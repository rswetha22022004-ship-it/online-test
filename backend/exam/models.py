from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    ROLE_ADMIN = "admin"
    ROLE_STUDENT = "student"
    ROLE_CHOICES = [
        (ROLE_ADMIN, "Admin"),
        (ROLE_STUDENT, "Student"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_STUDENT)
    phone_number = models.CharField(max_length=20, blank=True, default="")

    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Test(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=30)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_tests",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Question(models.Model):
    OPTION_CHOICES = [
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("D", "D"),
    ]

    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    option_a = models.CharField(max_length=300)
    option_b = models.CharField(max_length=300)
    option_c = models.CharField(max_length=300)
    option_d = models.CharField(max_length=300)
    correct_option = models.CharField(max_length=1, choices=OPTION_CHOICES)

    def __str__(self):
        return f"{self.test.title} - {self.text[:50]}"


class Attempt(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="attempts")
    score = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.student.username} - {self.test.title} ({self.score}/{self.total})"


class AttemptAnswer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="attempt_answers",
    )
    selected_option = models.CharField(max_length=1, choices=Question.OPTION_CHOICES)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.attempt_id} - Q{self.question_id}"


class SMSNotification(models.Model):
    STATUS_SENT = "sent"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_SENT, "Sent"),
        (STATUS_FAILED, "Failed"),
    ]

    attempt = models.ForeignKey(
        Attempt,
        on_delete=models.CASCADE,
        related_name="sms_notifications",
    )
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_sms_notifications",
    )
    phone_number = models.CharField(max_length=20, blank=True, default="")
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SENT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.attempt.student.username} - {self.status}"

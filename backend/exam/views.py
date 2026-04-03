import json
import re

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Attempt, AttemptAnswer, Question, SMSNotification, Test, UserProfile


STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "that",
    "this",
    "into",
    "your",
    "you",
    "are",
    "was",
    "were",
    "will",
    "have",
    "has",
    "had",
    "but",
    "not",
    "can",
    "use",
    "using",
    "about",
    "what",
    "when",
    "where",
    "which",
    "why",
    "how",
    "their",
    "there",
    "than",
    "then",
    "also",
    "all",
    "any",
    "each",
    "exam",
    "test",
}


def _json_body(request):
    try:
        return json.loads(request.body.decode("utf-8")) if request.body else {}
    except json.JSONDecodeError:
        return {}


def _json_error(message, status=400):
    return JsonResponse({"error": message}, status=status)


def _user_from_header(request):
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return None
    try:
        return User.objects.get(pk=int(user_id))
    except (ValueError, User.DoesNotExist):
        return None


def _role(user):
    if not user:
        return None
    profile = getattr(user, "profile", None)
    return profile.role if profile else None


def _extract_topics(syllabus_text):
    words = re.findall(r"[A-Za-z][A-Za-z0-9+#.-]{2,}", syllabus_text.lower())
    freq = {}
    for word in words:
        if word in STOP_WORDS:
            continue
        freq[word] = freq.get(word, 0) + 1
    ranked = sorted(freq.items(), key=lambda x: (-x[1], x[0]))
    return [topic for topic, _ in ranked[:8]]


def _generate_important_questions(topics):
    if not topics:
        return []

    patterns = [
        "Explain the core concept of '{topic}' with one practical example.",
        "Compare '{topic}' with a related concept and highlight key differences.",
        "What are common mistakes students make in '{topic}' and how to avoid them?",
        "Write a short note on real-world applications of '{topic}'.",
        "Design an exam-level problem based on '{topic}' and provide the ideal approach.",
    ]

    questions = []
    for idx, topic in enumerate(topics):
        template = patterns[idx % len(patterns)]
        questions.append(
            {
                "topic": topic,
                "question": template.format(topic=topic),
                "priority": "High" if idx < 3 else "Medium",
            }
        )
    return questions


@csrf_exempt
@require_http_methods(["POST"])
def login_view(request):
    payload = _json_body(request)
    username = payload.get("username", "").strip()
    password = payload.get("password", "")
    if not username or not password:
        return _json_error("Username and password are required.")

    user = authenticate(username=username, password=password)
    if not user:
        default_student_password = f"{username}123"
        if password == default_student_password:
            existing_user = User.objects.filter(username=username).first()
            if existing_user:
                profile, _ = UserProfile.objects.get_or_create(user=existing_user)
                if profile.role == UserProfile.ROLE_STUDENT:
                    existing_user.set_password(default_student_password)
                    existing_user.save(update_fields=["password"])
                    user = authenticate(username=username, password=default_student_password)
            else:
                created_user = User.objects.create_user(
                    username=username,
                    password=default_student_password,
                )
                UserProfile.objects.get_or_create(
                    user=created_user,
                    defaults={"role": UserProfile.ROLE_STUDENT},
                )
                user = created_user

    if not user:
        return _json_error("Invalid credentials.", status=401)

    profile, _ = UserProfile.objects.get_or_create(user=user)
    return JsonResponse(
        {
            "message": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": profile.role,
            },
        }
    )


@require_http_methods(["GET"])
def list_tests(request):
    tests = (
        Test.objects.all()
        .select_related("created_by")
        .prefetch_related("questions")
        .order_by("-created_at")
    )
    data = [
        {
            "id": test.id,
            "title": test.title,
            "description": test.description,
            "duration_minutes": test.duration_minutes,
            "created_by": test.created_by.username,
            "question_count": test.questions.count(),
        }
        for test in tests
    ]
    return JsonResponse({"tests": data})


@csrf_exempt
@require_http_methods(["POST"])
def create_test(request):
    user = _user_from_header(request)
    if not user:
        return _json_error("Unauthorized.", status=401)
    if _role(user) != UserProfile.ROLE_ADMIN:
        return _json_error("Only admin can create tests.", status=403)

    payload = _json_body(request)
    title = payload.get("title", "").strip()
    description = payload.get("description", "").strip()
    duration_minutes = int(payload.get("duration_minutes", 30))
    questions = payload.get("questions", [])

    if not title:
        return _json_error("Title is required.")
    if not questions:
        return _json_error("At least one question is required.")

    test = Test.objects.create(
        title=title,
        description=description,
        duration_minutes=duration_minutes,
        created_by=user,
    )

    for q in questions:
        Question.objects.create(
            test=test,
            text=q.get("text", ""),
            option_a=q.get("option_a", ""),
            option_b=q.get("option_b", ""),
            option_c=q.get("option_c", ""),
            option_d=q.get("option_d", ""),
            correct_option=q.get("correct_option", "A"),
        )

    return JsonResponse({"message": "Test created.", "test_id": test.id}, status=201)


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_test(request, test_id):
    user = _user_from_header(request)
    if not user:
        return _json_error("Unauthorized.", status=401)
    if _role(user) != UserProfile.ROLE_ADMIN:
        return _json_error("Only admin can delete tests.", status=403)

    try:
        test = Test.objects.get(pk=test_id)
    except Test.DoesNotExist:
        return _json_error("Test not found.", status=404)

    test_title = test.title
    test.delete()
    return JsonResponse({"message": f"Test '{test_title}' deleted successfully."})


@require_http_methods(["GET"])
def test_detail_for_student(request, test_id):
    user = _user_from_header(request)
    if not user:
        return _json_error("Unauthorized.", status=401)
    if _role(user) != UserProfile.ROLE_STUDENT:
        return _json_error("Only students can attend tests.", status=403)

    try:
        test = Test.objects.prefetch_related("questions").get(pk=test_id)
    except Test.DoesNotExist:
        return _json_error("Test not found.", status=404)

    if Attempt.objects.filter(student=user, test=test).exists():
        return _json_error("You have already submitted this test.", status=409)

    return JsonResponse(
        {
            "id": test.id,
            "title": test.title,
            "description": test.description,
            "duration_minutes": test.duration_minutes,
            "questions": [
                {
                    "id": q.id,
                    "text": q.text,
                    "option_a": q.option_a,
                    "option_b": q.option_b,
                    "option_c": q.option_c,
                    "option_d": q.option_d,
                }
                for q in test.questions.all()
            ],
        }
    )


@csrf_exempt
@require_http_methods(["POST"])
def submit_test(request, test_id):
    user = _user_from_header(request)
    if not user:
        return _json_error("Unauthorized.", status=401)
    if _role(user) != UserProfile.ROLE_STUDENT:
        return _json_error("Only students can submit tests.", status=403)

    try:
        test = Test.objects.prefetch_related("questions").get(pk=test_id)
    except Test.DoesNotExist:
        return _json_error("Test not found.", status=404)

    if Attempt.objects.filter(student=user, test=test).exists():
        return _json_error("Test already submitted.", status=409)

    payload = _json_body(request)
    answers_payload = payload.get("answers", [])
    answers_lookup = {
        int(item["question_id"]): item.get("selected_option", "")
        for item in answers_payload
        if "question_id" in item
    }

    questions = list(test.questions.all())
    total = len(questions)
    score = 0

    attempt = Attempt.objects.create(student=user, test=test, total=total)
    for question in questions:
        selected = answers_lookup.get(question.id, "")
        correct = selected == question.correct_option
        if correct:
            score += 1
        AttemptAnswer.objects.create(
            attempt=attempt,
            question=question,
            selected_option=selected if selected in {"A", "B", "C", "D"} else "A",
            is_correct=correct,
        )

    attempt.score = score
    attempt.save(update_fields=["score"])

    return JsonResponse(
        {
            "message": "Test submitted successfully.",
            "result": {"score": score, "total": total},
        }
    )


@require_http_methods(["GET"])
def student_results(request):
    user = _user_from_header(request)
    if not user:
        return _json_error("Unauthorized.", status=401)
    if _role(user) != UserProfile.ROLE_STUDENT:
        return _json_error("Only students can view this endpoint.", status=403)

    attempts = Attempt.objects.filter(student=user).select_related("test")
    data = [
        {
            "test_id": attempt.test_id,
            "test_title": attempt.test.title,
            "score": attempt.score,
            "total": attempt.total,
            "submitted_at": attempt.submitted_at,
        }
        for attempt in attempts
    ]
    return JsonResponse({"results": data})


@require_http_methods(["GET"])
def student_messages(request):
    user = _user_from_header(request)
    if not user:
        return _json_error("Unauthorized.", status=401)
    if _role(user) != UserProfile.ROLE_STUDENT:
        return _json_error("Only students can view this endpoint.", status=403)

    notifications = (
        SMSNotification.objects.filter(attempt__student=user)
        .select_related("attempt", "attempt__test")
        .order_by("-created_at")
    )
    data = [
        {
            "id": notification.id,
            "test_title": notification.attempt.test.title,
            "message": notification.message,
            "status": notification.status,
            "sent_at": notification.created_at,
        }
        for notification in notifications
    ]
    return JsonResponse({"messages": data})


@require_http_methods(["GET"])
def admin_results(request):
    user = _user_from_header(request)
    if not user:
        return _json_error("Unauthorized.", status=401)
    if _role(user) != UserProfile.ROLE_ADMIN:
        return _json_error("Only admin can view all results.", status=403)

    attempts = Attempt.objects.select_related("student", "test")
    data = [
        {
            "attempt_id": attempt.id,
            "student": attempt.student.username,
            "test_title": attempt.test.title,
            "score": attempt.score,
            "total": attempt.total,
            "percentage": round((attempt.score / attempt.total) * 100, 2)
            if attempt.total
            else 0,
            "submitted_at": attempt.submitted_at,
        }
        for attempt in attempts
    ]
    return JsonResponse({"results": data})


@csrf_exempt
@require_http_methods(["POST"])
def generate_questions_from_syllabus(request):
    user = _user_from_header(request)
    if not user:
        return _json_error("Unauthorized.", status=401)
    if _role(user) != UserProfile.ROLE_ADMIN:
        return _json_error("Only admin can use this endpoint.", status=403)

    payload = _json_body(request)
    syllabus = payload.get("syllabus", "").strip()
    if not syllabus:
        return _json_error("Syllabus text is required.")

    topics = _extract_topics(syllabus)
    questions = _generate_important_questions(topics)

    if not questions:
        return JsonResponse(
            {
                "topics": [],
                "important_questions": [],
                "message": "No major topics detected. Please provide more syllabus details.",
            }
        )

    return JsonResponse({"topics": topics, "important_questions": questions})


@csrf_exempt
@require_http_methods(["POST"])
def send_congratulation_sms(request, attempt_id):
    user = _user_from_header(request)
    if not user:
        return _json_error("Unauthorized.", status=401)
    if _role(user) != UserProfile.ROLE_ADMIN:
        return _json_error("Only admin can send congratulation SMS.", status=403)

    try:
        attempt = Attempt.objects.select_related("student", "test", "student__profile").get(
            pk=attempt_id
        )
    except Attempt.DoesNotExist:
        return _json_error("Attempt not found.", status=404)

    if attempt.total == 0:
        return _json_error("Invalid attempt score data.", status=400)

    percentage = (attempt.score / attempt.total) * 100
    payload = _json_body(request)
    try:
        min_percentage = float(payload.get("min_percentage", 70))
    except (TypeError, ValueError):
        return _json_error("Minimum percentage must be a valid number.", status=400)
    if percentage < min_percentage:
        return _json_error(
            f"Student score is {percentage:.2f}%, below threshold {min_percentage:.2f}%.",
            status=400,
        )

    message = (
        f"Congratulations {attempt.student.username}! "
        f"You scored {attempt.score}/{attempt.total} ({percentage:.2f}%) in "
        f"'{attempt.test.title}'. Keep it up!"
    )

    SMSNotification.objects.create(
        attempt=attempt,
        sent_by=user,
        phone_number="",
        message=message,
        status=SMSNotification.STATUS_SENT,
    )

    # Demo provider: stores congratulation notifications in database.
    return JsonResponse(
        {
            "message": "Congratulations message sent successfully.",
            "percentage": round(percentage, 2),
        }
    )

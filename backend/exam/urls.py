from django.urls import path

from .views import (
    admin_results,
    create_test,
    delete_test,
    generate_questions_from_syllabus,
    list_tests,
    login_view,
    send_congratulation_sms,
    student_messages,
    student_results,
    submit_test,
    test_detail_for_student,
)

urlpatterns = [
    path("login/", login_view, name="login"),
    path("tests/", list_tests, name="list_tests"),
    path("tests/create/", create_test, name="create_test"),
    path("tests/<int:test_id>/delete/", delete_test, name="delete_test"),
    path("tests/<int:test_id>/", test_detail_for_student, name="test_detail_for_student"),
    path("tests/<int:test_id>/submit/", submit_test, name="submit_test"),
    path("results/", student_results, name="student_results"),
    path("results/messages/", student_messages, name="student_messages"),
    path("admin/results/", admin_results, name="admin_results"),
    path(
        "admin/results/<int:attempt_id>/send-congrats-sms/",
        send_congratulation_sms,
        name="send_congratulation_sms",
    ),
    path(
        "admin/syllabus/questions/",
        generate_questions_from_syllabus,
        name="generate_questions_from_syllabus",
    ),
]

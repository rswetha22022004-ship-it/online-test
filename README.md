Frontend (React + Vite)

Bootstrapping:
[index.html](/d:/Online Test/online_test/frontend/index.html)
[main.jsx](/d:/Online Test/online_test/frontend/src/main.jsx)
[vite.config.js](/d:/Online Test/online_test/frontend/vite.config.js)

API client wrapper:
[api.js](/d:/Online Test/online_test/frontend/src/api.js)

Base URL: http://localhost:8000/api
Adds X-User-Id for “authenticated” calls
Throws backend error messages for UI display
Main app/UI logic:
[App.jsx](/d:/Online Test/online_test/frontend/src/App.jsx)

Stores logged-in user in localStorage (exam_user)
Switches UI by role:
admin -> test creation, results view, syllabus tool, send messages
student -> list tests, start/submit test, view results/messages
Polls student messages every 10s
Styling/assets:
[styles.css](/d:/Online Test/online_test/frontend/src/styles.css)
Uses different backgrounds for login/student pages and card-based layout.

End-to-End Flow

User logs in from React.
Django returns user id/role.
Frontend stores user and sends X-User-Id in later requests.
Admin creates tests; students fetch and attempt once.
Submission creates Attempt + AttemptAnswer, computes score.
Admin can send congratulation notification above threshold; student sees it in “Your Messages”.

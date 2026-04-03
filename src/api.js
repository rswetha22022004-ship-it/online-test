const API_BASE = "http://localhost:8000/api";

async function apiRequest(path, options = {}, user) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (user?.id) {
    headers["X-User-Id"] = String(user.id);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || "Request failed");
  }
  return data;
}

export function login(username, password) {
  return apiRequest("/login/", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function listTests() {
  return apiRequest("/tests/");
}

export function createTest(payload, user) {
  return apiRequest(
    "/tests/create/",
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    user
  );
}

export function deleteTest(testId, user) {
  return apiRequest(
    `/tests/${testId}/delete/`,
    {
      method: "DELETE",
    },
    user
  );
}

export function getStudentTest(testId, user) {
  return apiRequest(`/tests/${testId}/`, {}, user);
}

export function submitTest(testId, answers, user) {
  return apiRequest(
    `/tests/${testId}/submit/`,
    {
      method: "POST",
      body: JSON.stringify({ answers }),
    },
    user
  );
}

export function getStudentResults(user) {
  return apiRequest("/results/", {}, user);
}

export function getStudentMessages(user) {
  return apiRequest("/results/messages/", {}, user);
}

export function getAdminResults(user) {
  return apiRequest("/admin/results/", {}, user);
}

export function generateImportantQuestions(syllabus, user) {
  return apiRequest(
    "/admin/syllabus/questions/",
    {
      method: "POST",
      body: JSON.stringify({ syllabus }),
    },
    user
  );
}

export function sendCongratulationMessage(attemptId, minPercentage, user) {
  return apiRequest(
    `/admin/results/${attemptId}/send-congrats-sms/`,
    {
      method: "POST",
      body: JSON.stringify({ min_percentage: minPercentage }),
    },
    user
  );
}

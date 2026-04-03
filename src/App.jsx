import { useEffect, useMemo, useState } from "react";
import {
  createTest,
  deleteTest,
  generateImportantQuestions,
  getAdminResults,
  getStudentMessages,
  getStudentResults,
  getStudentTest,
  listTests,
  login,
  sendCongratulationMessage,
  submitTest,
} from "./api";

const emptyQuestion = () => ({
  text: "",
  option_a: "",
  option_b: "",
  option_c: "",
  option_d: "",
  correct_option: "A",
});

export default function App() {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("exam_user");
    return raw ? JSON.parse(raw) : null;
  });
  const [error, setError] = useState("");

  useEffect(() => {
    if (user) {
      localStorage.setItem("exam_user", JSON.stringify(user));
    } else {
      localStorage.removeItem("exam_user");
    }
  }, [user]);

  const onLogout = () => {
    setError("");
    setUser(null);
  };

  return (
    <div
      className={`page ${!user ? "login-page" : ""} ${
        user?.role === "student" ? "student-page" : ""
      }`}
    >
      <div className="container">
        <header className="header">
          <h1>Online Exam Portal</h1>
          <p>Welcome to your online test dashboard</p>
        </header>

        {error && <div className="alert">{error}</div>}

        {!user ? (
          <LoginCard
            onLogin={async (username, password) => {
              try {
                setError("");
                const data = await login(username, password);
                setUser(data.user);
              } catch (e) {
                setError(e.message);
              }
            }}
          />
        ) : user.role === "admin" ? (
          <AdminDashboard user={user} onError={setError} />
        ) : (
          <StudentDashboard user={user} onError={setError} />
        )}

        {user && (
          <div className="logout-bottom">
            <button className="btn secondary" onClick={onLogout}>
              Logout ({user.username})
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function LoginCard({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onLogin(username, password);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="card">
      <h2>Login</h2>
      <form onSubmit={submit} className="stack">
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Username"
          required
        />
        <input
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Password"
          type="password"
          required
        />
        <button className="btn" disabled={loading}>
          {loading ? "Signing in..." : "Sign In"}
        </button>
      </form>
    </section>
  );
}

function AdminDashboard({ user, onError }) {
  const [tests, setTests] = useState([]);
  const [results, setResults] = useState([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [duration, setDuration] = useState(30);
  const [questions, setQuestions] = useState([emptyQuestion()]);
  const [syllabus, setSyllabus] = useState("");
  const [suggested, setSuggested] = useState([]);
  const [topics, setTopics] = useState([]);
  const [generating, setGenerating] = useState(false);
  const [messageThreshold, setMessageThreshold] = useState(50);
  const [messageInfo, setMessageInfo] = useState("");

  const loadData = async () => {
    try {
      onError("");
      const [testsData, resultsData] = await Promise.all([
        listTests(),
        getAdminResults(user),
      ]);
      setTests(testsData.tests);
      setResults(resultsData.results);
    } catch (e) {
      onError(e.message);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const addQuestion = () => setQuestions((prev) => [...prev, emptyQuestion()]);

  const updateQuestion = (index, key, value) => {
    setQuestions((prev) =>
      prev.map((q, i) => (i === index ? { ...q, [key]: value } : q))
    );
  };

  const submit = async (e) => {
    e.preventDefault();
    try {
      onError("");
      setMessageInfo("");
      await createTest(
        {
          title,
          description,
          duration_minutes: Number(duration),
          questions,
        },
        user
      );
      setTitle("");
      setDescription("");
      setDuration(30);
      setQuestions([emptyQuestion()]);
      await loadData();
    } catch (e) {
      onError(e.message);
    }
  };

  const generateFromSyllabus = async (e) => {
    e.preventDefault();
    try {
      onError("");
      setMessageInfo("");
      setGenerating(true);
      const data = await generateImportantQuestions(syllabus, user);
      setSuggested(data.important_questions || []);
      setTopics(data.topics || []);
    } catch (e) {
      onError(e.message);
    } finally {
      setGenerating(false);
    }
  };

  const sendCongrats = async (attemptId) => {
    try {
      onError("");
      const data = await sendCongratulationMessage(
        attemptId,
        Number(messageThreshold),
        user
      );
      setMessageInfo(`Congratulation message sent for score ${data.percentage}% successfully.`);
    } catch (e) {
      onError(e.message);
    }
  };

  const removeTest = async (testId, testTitle) => {
    const shouldDelete = window.confirm(
      `Delete test "${testTitle}"? This will remove related questions and attempts.`
    );
    if (!shouldDelete) {
      return;
    }

    try {
      onError("");
      setMessageInfo("");
      await deleteTest(testId, user);
      await loadData();
    } catch (e) {
      onError(e.message);
    }
  };

  return (
    <div className="grid">
      <section className="card">
        <h2>Create Test</h2>
        <form onSubmit={submit} className="stack">
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Test title"
            required
          />
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description"
          />
          <input
            type="number"
            value={duration}
            min={1}
            onChange={(e) => setDuration(e.target.value)}
          />
          {questions.map((q, idx) => (
            <div key={idx} className="question-box">
              <h4>Question {idx + 1}</h4>
              <textarea
                value={q.text}
                onChange={(e) => updateQuestion(idx, "text", e.target.value)}
                placeholder="Question text"
                required
              />
              <input
                value={q.option_a}
                onChange={(e) => updateQuestion(idx, "option_a", e.target.value)}
                placeholder="Option A"
                required
              />
              <input
                value={q.option_b}
                onChange={(e) => updateQuestion(idx, "option_b", e.target.value)}
                placeholder="Option B"
                required
              />
              <input
                value={q.option_c}
                onChange={(e) => updateQuestion(idx, "option_c", e.target.value)}
                placeholder="Option C"
                required
              />
              <input
                value={q.option_d}
                onChange={(e) => updateQuestion(idx, "option_d", e.target.value)}
                placeholder="Option D"
                required
              />
              <select
                value={q.correct_option}
                onChange={(e) =>
                  updateQuestion(idx, "correct_option", e.target.value)
                }
              >
                <option value="A">Correct: A</option>
                <option value="B">Correct: B</option>
                <option value="C">Correct: C</option>
                <option value="D">Correct: D</option>
              </select>
            </div>
          ))}
          <div className="row">
            <button type="button" className="btn secondary" onClick={addQuestion}>
              Add Question
            </button>
            <button className="btn">Create Test</button>
          </div>
        </form>
      </section>

      <section className="card">
        <h2>Tests</h2>
        <ul className="list">
          {tests.map((test) => (
            <li key={test.id}>
              <div>
                <strong>{test.title}</strong> ({test.question_count} questions)
              </div>
              <button
                className="btn secondary"
                onClick={() => removeTest(test.id, test.title)}
              >
                Delete
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="card">
        <h2>Student Results</h2>
        <div className="row">
          <input
            type="number"
            min={1}
            max={100}
            value={messageThreshold}
            onChange={(e) => setMessageThreshold(e.target.value)}
            placeholder="Minimum %"
          />
        </div>
        <p className="muted">
          Send congratulation message for students scoring at least {messageThreshold}%.
        </p>
        {messageInfo && <p className="success">{messageInfo}</p>}
        <ul className="list">
          {results.map((r, idx) => (
            <li key={idx}>
              <div>
                {r.student} - {r.test_title}: {r.score}/{r.total} ({r.percentage}%)
                {r.percentage < Number(messageThreshold) && (
                  <div className="muted">
                    Current score is below minimum {messageThreshold}%. Lower minimum % to send.
                  </div>
                )}
              </div>
              <button
                className="btn secondary"
                disabled={r.percentage < Number(messageThreshold)}
                onClick={() => sendCongrats(r.attempt_id)}
              >
                {r.percentage < Number(messageThreshold) ? "Not Eligible" : "Send Message"}
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="card wide">
        <h2>Syllabus to Important Questions</h2>
        <form className="stack" onSubmit={generateFromSyllabus}>
          <textarea
            value={syllabus}
            onChange={(e) => setSyllabus(e.target.value)}
            placeholder="Paste syllabus here..."
            rows={5}
            required
          />
          <div className="row">
            <button className="btn" disabled={generating}>
              {generating ? "Generating..." : "Generate Important Questions"}
            </button>
          </div>
        </form>

        {topics.length > 0 && (
          <p className="muted">
            Detected topics: {topics.join(", ")}
          </p>
        )}

        {suggested.length > 0 && (
          <ul className="list top-space">
            {suggested.map((item, idx) => (
              <li key={idx}>
                <div>
                  <strong>{item.priority}</strong> | {item.topic}
                  <br />
                  {item.question}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function StudentDashboard({ user, onError }) {
  const [tests, setTests] = useState([]);
  const [results, setResults] = useState([]);
  const [messages, setMessages] = useState([]);
  const [activeTest, setActiveTest] = useState(null);
  const [answers, setAnswers] = useState({});
  const [shakeCard, setShakeCard] = useState("");

  const loadData = async () => {
    try {
      onError("");
      const [testsData, resultData, messagesData] = await Promise.all([
        listTests(),
        getStudentResults(user),
        getStudentMessages(user),
      ]);
      setTests(testsData.tests);
      setResults(resultData.results);
      setMessages(messagesData.messages || []);
    } catch (e) {
      onError(e.message);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    const intervalId = window.setInterval(async () => {
      try {
        const messagesData = await getStudentMessages(user);
        setMessages(messagesData.messages || []);
      } catch {
        // Keep background refresh silent; normal errors still show on explicit actions.
      }
    }, 10000);

    return () => window.clearInterval(intervalId);
  }, [user]);

  const attemptedTestIds = useMemo(
    () => new Set(results.map((r) => r.test_id)),
    [results]
  );

  const startTest = async (testId) => {
    try {
      onError("");
      const data = await getStudentTest(testId, user);
      setActiveTest(data);
      setAnswers({});
    } catch (e) {
      onError(e.message);
    }
  };

  const submitActiveTest = async () => {
    try {
      onError("");
      const answersArray = Object.entries(answers).map(([question_id, selected]) => ({
        question_id: Number(question_id),
        selected_option: selected,
      }));
      await submitTest(activeTest.id, answersArray, user);
      setActiveTest(null);
      setAnswers({});
      await loadData();
    } catch (e) {
      onError(e.message);
    }
  };

  const triggerShake = (cardName) => {
    setShakeCard(cardName);
    window.setTimeout(() => setShakeCard(""), 350);
  };

  return (
    <div className="grid">
      <section
        className={`card ${shakeCard === "tests" ? "shake" : ""}`}
        onClick={() => triggerShake("tests")}
      >
        <h2>Available Tests</h2>
        <ul className="list">
          {tests.map((test) => (
            <li key={test.id}>
              <div>
                <strong>{test.title}</strong> ({test.question_count} questions)
              </div>
              <button
                className="btn"
                disabled={attemptedTestIds.has(test.id)}
                onClick={() => startTest(test.id)}
              >
                {attemptedTestIds.has(test.id) ? "Attempted" : "Start"}
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section
        className={`card ${shakeCard === "results" ? "shake" : ""}`}
        onClick={() => triggerShake("results")}
      >
        <h2>Your Results</h2>
        <ul className="list">
          {results.map((r) => (
            <li key={r.test_id}>
              {r.test_title}: {r.score}/{r.total}
            </li>
          ))}
        </ul>
      </section>

      <section className="card">
        <h2>Your Messages</h2>
        {messages.length === 0 ? (
          <p className="muted">No congratulation messages yet.</p>
        ) : (
          <ul className="list">
            {messages.map((m) => (
              <li key={m.id}>
                <div>
                  <strong>{m.test_title}</strong>
                  <br />
                  {m.message}
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>

      {activeTest && (
        <section className="card wide">
          <h2>{activeTest.title}</h2>
          <p className="muted">{activeTest.description}</p>
          {activeTest.questions.map((q, idx) => (
            <div className="question-box" key={q.id}>
              <h4>
                Q{idx + 1}. {q.text}
              </h4>
              {["A", "B", "C", "D"].map((opt) => (
                <label key={opt} className="option">
                  <input
                    type="radio"
                    name={`question-${q.id}`}
                    checked={answers[q.id] === opt}
                    onChange={() =>
                      setAnswers((prev) => ({
                        ...prev,
                        [q.id]: opt,
                      }))
                    }
                  />
                  {opt}. {q[`option_${opt.toLowerCase()}`]}
                </label>
              ))}
            </div>
          ))}
          <button className="btn" onClick={submitActiveTest}>
            Submit Test
          </button>
        </section>
      )}
    </div>
  );
}

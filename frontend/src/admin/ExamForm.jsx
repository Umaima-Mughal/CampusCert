import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { createExam, fetchExam, updateExam } from "../api/exams";
import {
  apiErrorMessage,
  distributionEntries,
  entriesToDistribution,
  toDateTimeLocal,
  toIsoOrNull,
} from "./examUtils";

const emptyForm = {
  name: "",
  duration_minutes: 60,
  description: "",
  instructions: "",
  passing_score: 50,
  max_attempts: 1,
  shuffle_questions: true,
  late_join_minutes: 0,
  starts_at: "",
  ends_at: "",
};

export default function ExamForm() {
  const { examId } = useParams();
  const isEdit = Boolean(examId);
  const navigate = useNavigate();
  const [form, setForm] = useState(emptyForm);
  const [distribution, setDistribution] = useState([{ subjectId: "", count: "" }]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(isEdit);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!isEdit) return undefined;
    let cancelled = false;
    fetchExam(examId)
      .then((exam) => {
        if (cancelled) return;
        setForm({
          name: exam.name || "",
          duration_minutes: exam.duration_minutes,
          description: exam.description || "",
          instructions: exam.instructions || "",
          passing_score: exam.passing_score ?? "",
          max_attempts: exam.max_attempts,
          shuffle_questions: exam.shuffle_questions,
          late_join_minutes: exam.late_join_minutes,
          starts_at: toDateTimeLocal(exam.starts_at),
          ends_at: toDateTimeLocal(exam.ends_at),
        });
        const entries = distributionEntries(exam.distribution);
        setDistribution(entries.length ? entries : [{ subjectId: "", count: "" }]);
      })
      .catch((err) => {
        if (!cancelled) setError(apiErrorMessage(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [examId, isEdit]);

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function updateDistribution(index, field, value) {
    setDistribution((current) =>
      current.map((row, i) => (i === index ? { ...row, [field]: value } : row))
    );
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    const duration = Number(form.duration_minutes);
    if (!form.name.trim() || form.name.trim().length < 2) {
      setError("Exam name must be at least 2 characters.");
      return;
    }
    if (!Number.isFinite(duration) || duration < 1) {
      setError("Duration must be at least 1 minute.");
      return;
    }

    const payload = {
      name: form.name.trim(),
      duration_minutes: duration,
      description: form.description.trim() || null,
      instructions: form.instructions.trim() || null,
      passing_score: form.passing_score === "" ? null : Number(form.passing_score),
      max_attempts: Number(form.max_attempts) || 1,
      shuffle_questions: Boolean(form.shuffle_questions),
      late_join_minutes: Number(form.late_join_minutes) || 0,
      starts_at: toIsoOrNull(form.starts_at),
      ends_at: toIsoOrNull(form.ends_at),
      distribution: entriesToDistribution(distribution),
    };

    if ((payload.starts_at && !payload.ends_at) || (!payload.starts_at && payload.ends_at)) {
      setError("Set both start and end times, or leave both empty.");
      return;
    }

    setSaving(true);
    try {
      const saved = isEdit ? await updateExam(examId, payload) : await createExam(payload);
      navigate(`/admin/exams/${saved.id}`);
    } catch (err) {
      setError(apiErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <p className="admin-muted">Loading exam...</p>;

  return (
    <div>
      <div className="admin-page-header">
        <div>
          <h3>{isEdit ? "Edit exam" : "Create exam"}</h3>
          <p>
            Configure duration, scheduling, passing score, and the subject counts
            Member 3 will use for randomized question sets.
          </p>
        </div>
        <Link to="/admin/exams" className="admin-btn secondary">Back to exams</Link>
      </div>

      {error && <div className="admin-alert error">{error}</div>}

      <form className="admin-card" onSubmit={handleSubmit}>
        <div className="admin-form">
          <div className="admin-field full">
            <label htmlFor="exam-name">Exam name</label>
            <input
              id="exam-name"
              value={form.name}
              onChange={(e) => updateField("name", e.target.value)}
              placeholder="Midterm — Discrete Mathematics"
              required
            />
          </div>
          <div className="admin-field">
            <label htmlFor="duration">Duration (minutes)</label>
            <input
              id="duration"
              type="number"
              min="1"
              max="600"
              value={form.duration_minutes}
              onChange={(e) => updateField("duration_minutes", e.target.value)}
              required
            />
          </div>
          <div className="admin-field">
            <label htmlFor="passing">Passing score (%)</label>
            <input
              id="passing"
              type="number"
              min="0"
              max="100"
              value={form.passing_score}
              onChange={(e) => updateField("passing_score", e.target.value)}
            />
          </div>
          <div className="admin-field">
            <label htmlFor="attempts">Max attempts</label>
            <input
              id="attempts"
              type="number"
              min="1"
              max="10"
              value={form.max_attempts}
              onChange={(e) => updateField("max_attempts", e.target.value)}
            />
          </div>
          <div className="admin-field">
            <label htmlFor="late-join">Late join (minutes)</label>
            <input
              id="late-join"
              type="number"
              min="0"
              max="180"
              value={form.late_join_minutes}
              onChange={(e) => updateField("late_join_minutes", e.target.value)}
            />
          </div>
          <div className="admin-field">
            <label htmlFor="starts">Starts at</label>
            <input
              id="starts"
              type="datetime-local"
              value={form.starts_at}
              onChange={(e) => updateField("starts_at", e.target.value)}
            />
          </div>
          <div className="admin-field">
            <label htmlFor="ends">Ends at</label>
            <input
              id="ends"
              type="datetime-local"
              value={form.ends_at}
              onChange={(e) => updateField("ends_at", e.target.value)}
            />
          </div>
          <div className="admin-field full">
            <label htmlFor="shuffle">
              <input
                id="shuffle"
                type="checkbox"
                checked={form.shuffle_questions}
                onChange={(e) => updateField("shuffle_questions", e.target.checked)}
                style={{ marginRight: 8 }}
              />
              Shuffle question order for each student (used by question selection / attempts)
            </label>
          </div>
          <div className="admin-field full">
            <label htmlFor="description">Description</label>
            <textarea
              id="description"
              value={form.description}
              onChange={(e) => updateField("description", e.target.value)}
              placeholder="Shown to admins and examiners when reviewing this sitting."
            />
          </div>
          <div className="admin-field full">
            <label htmlFor="instructions">Student instructions</label>
            <textarea
              id="instructions"
              value={form.instructions}
              onChange={(e) => updateField("instructions", e.target.value)}
              placeholder="Instructions displayed before the attempt starts."
            />
          </div>
          <div className="admin-field full">
            <label>Question distribution</label>
            <p className="admin-help">
              Optional subject IDs and counts. Member 3’s question bank will use this
              map when generating randomized papers. Leave empty until subjects exist.
            </p>
            {distribution.map((row, index) => (
              <div className="admin-distribution-row" key={`dist-${index}`}>
                <input
                  value={row.subjectId}
                  onChange={(e) => updateDistribution(index, "subjectId", e.target.value)}
                  placeholder="Subject ID"
                />
                <input
                  type="number"
                  min="1"
                  value={row.count}
                  onChange={(e) => updateDistribution(index, "count", e.target.value)}
                  placeholder="Count"
                />
                <button
                  type="button"
                  className="admin-btn secondary small"
                  onClick={() =>
                    setDistribution((current) => current.filter((_, i) => i !== index))
                  }
                  disabled={distribution.length === 1}
                >
                  Remove
                </button>
              </div>
            ))}
            <button
              type="button"
              className="admin-btn secondary small"
              onClick={() => setDistribution((current) => [...current, { subjectId: "", count: "" }])}
            >
              Add subject count
            </button>
          </div>
        </div>
        <div className="admin-actions" style={{ marginTop: 18 }}>
          <button type="submit" className="admin-btn" disabled={saving}>
            {saving ? "Saving..." : isEdit ? "Save changes" : "Create exam"}
          </button>
        </div>
      </form>
    </div>
  );
}

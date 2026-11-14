import { useCallback, useEffect, useRef, useState } from "react";
import { Navigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { bulkDeleteQuestions, deleteQuestion, getFilterOptions, importQuestions, listQuestions } from "../api/questionsApi";
import ErrorBoundary from "./ErrorBoundary";
import McqBlock from "./McqBlock";
import PaperEditor from "./PaperEditor";
import PaperGenerator from "./PaperGenerator";
import PapersView from "./PapersView";
import "./QuestionBank.css";

const PAGE_SIZE = 20;
const EMPTY = { subject: "", topic: "", difficulty: "", q: "" };

const BANK_ROLES = ["examiner", "super_admin"];

// Only examiners build the question bank (the API enforces it too). Admins just pick a paper for an exam.
export default function QuestionBank() {
  const { user, loading } = useAuth();
  if (loading) return <p style={{ textAlign: "center", marginTop: 40 }}>Loading...</p>;
  if (!user) return <Navigate to="/login" replace />;
  if (!BANK_ROLES.includes(user.role)) return <Navigate to={user.role === "admin" ? "/admin" : "/"} replace />;
  return <ErrorBoundary><QuestionBankInner /></ErrorBoundary>;
}

function QuestionBankInner() {
  const { user, logout } = useAuth();
  const [searchParams] = useSearchParams();
  const paperFromUrl = Number(searchParams.get("paper")) || null;   // /question-bank?paper=12 opens that paper
  const [filters, setFilters] = useState(EMPTY);
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ items: [], total: 0 });
  const [options, setOptions] = useState({ subjects: [], topics: [], difficulties: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [report, setReport] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const fileRef = useRef(null);
  const [tab, setTab] = useState(paperFromUrl ? "papers" : "bank");            // bank | generate | papers
  const [basket, setBasket] = useState({});          // questions ticked for a new paper: { id: question }
  const [draft, setDraft] = useState(null);          // items for the paper editor, or null
  const [focusPaperId, setFocusPaperId] = useState(paperFromUrl);
  const [allMatching, setAllMatching] = useState(false);   // "select all N" across every page
  const [deleting, setDeleting] = useState(false);
  const [notice, setNotice] = useState("");
  const [rejected, setRejected] = useState(null);   // an import file that was refused: { fileName, message, errors, total }

  // debounce the search box so we don't hit the API on every keystroke
  const [search, setSearch] = useState("");
  useEffect(() => {
    const t = setTimeout(() => { setFilters((f) => ({ ...f, q: search })); setPage(1); setAllMatching(false); }, 300);
    return () => clearTimeout(t);
  }, [search]);

  const loadQuestions = useCallback(async () => {
    setLoading(true); setError("");
    try { setData(await listQuestions({ ...filters, page, page_size: PAGE_SIZE })); }
    catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [filters, page]);

  const loadOptions = useCallback(
    () => getFilterOptions(filters.subject).then(setOptions).catch(() => {}), [filters.subject]);

  useEffect(() => { loadQuestions(); }, [loadQuestions]);
  useEffect(() => { loadOptions(); }, [loadOptions]);

  const setFilter = (key, value) => {
    setFilters((f) => ({ ...f, [key]: value, ...(key === "subject" ? { topic: "" } : {}) }));
    setPage(1);
    setAllMatching(false);
  };
  const clearAll = () => { setFilters(EMPTY); setSearch(""); setPage(1); setAllMatching(false); };
  const hasFilters = Object.values(filters).some(Boolean);

  async function upload(file) {
    if (!file) return;
    setUploading(true); setReport(null); setError(""); setRejected(null); setNotice("");
    try {
      setReport({ ...(await importQuestions(file)), fileName: file.name });
      setPage(1); await Promise.all([loadQuestions(), loadOptions()]);
    } catch (e) {
      if (e.errors) setRejected({ fileName: file.name, message: e.message, errors: e.errors, total: e.totalErrors });
      else setError(e.message);
    }
    finally { setUploading(false); if (fileRef.current) fileRef.current.value = ""; }
  }

  async function remove(row) {
    if (deleting) return;
    if (!window.confirm("Delete this question? This can't be undone.")) return;
    setDeleting(true); setError(""); setNotice("");
    try { await deleteQuestion(row.id); setBasket((b) => { const n = { ...b }; delete n[row.id]; return n; }); await Promise.all([loadQuestions(), loadOptions()]); }
    catch (e) {
      await Promise.all([loadQuestions(), loadOptions()]);   // the row may already be gone: show the real list
      setError(e.message);
    }
    finally { setDeleting(false); }
  }

  const pages = Math.max(1, Math.ceil(data.total / PAGE_SIZE));

  const selectedCount = allMatching ? data.total : Object.keys(basket).length;
  const allOnPage = data.items.length > 0 && (allMatching || data.items.every((r) => basket[r.id]));
  const isTicked = (r) => allMatching || !!basket[r.id];
  const toggleRow = (r) => {
    if (allMatching) {                      // unticking one row leaves "select all" and keeps this page minus the row
      const rest = {};
      data.items.forEach((x) => { if (x.id !== r.id) rest[x.id] = x; });
      setAllMatching(false); setBasket(rest);
      return;
    }
    setBasket((b) => {
      const n = { ...b };
      if (n[r.id]) delete n[r.id]; else n[r.id] = r;
      return n;
    });
  };
  const togglePage = () => {
    if (allMatching) { setAllMatching(false); setBasket({}); return; }
    setBasket((b) => {
      const n = { ...b };
      data.items.forEach((r) => { if (allOnPage) delete n[r.id]; else n[r.id] = r; });
      return n;
    });
  };
  const clearSelection = () => { setAllMatching(false); setBasket({}); };
  // every row of this page is ticked, but more questions exist on other pages
  const offerSelectAll = allOnPage && !allMatching && data.total > data.items.length;

  // all = true  -> every question that matches the current filters (the whole bank if there are none)
  // all = false -> only the ticked questions
  async function bulkDelete(all) {
    const count = all ? data.total : Object.keys(basket).length;
    if (count === 0 || deleting) return;
    const scope = all ? (hasFilters ? " that match your filters" : " (your ENTIRE question bank)") : "";
    if (!window.confirm(`Delete ${count} question${count === 1 ? "" : "s"}${scope}? This can't be undone. They are also removed from exam papers.`)) return;
    if (all && !hasFilters) {
      const typed = window.prompt(`This empties your whole question bank (${count} questions). Type DELETE to confirm.`);
      if (typed === null || typed.trim() !== "DELETE") return;
    }
    setDeleting(true); setError(""); setNotice(""); setReport(null); setRejected(null);
    try {
      const body = all
        ? { all_matching: true, ...Object.fromEntries(Object.entries(filters).filter(([, v]) => v)) }
        : { ids: Object.keys(basket).map(Number) };
      const { deleted } = await bulkDeleteQuestions(body);
      clearSelection(); setPage(1);
      await Promise.all([loadQuestions(), loadOptions()]);
      setNotice(`${deleted} question${deleted === 1 ? "" : "s"} deleted.`);
    } catch (e) { setError(e.message); }
    finally { setDeleting(false); }
  }
  const deleteSelected = () => bulkDelete(allMatching);

  // after a paper is created or saved: leave the editor/generator and open that paper in "Exam papers"
  const showPaper = (p) => { setDraft(null); setBasket({}); setAllMatching(false); setFocusPaperId(p.id); setTab("papers"); };

  if (draft) {
    return (
      <div className="qb">
        <PaperEditor initialItems={draft} onCancel={() => setDraft(null)} onSaved={showPaper} />
      </div>
    );
  }

  return (
    <div className="qb">
      <header className="qb-head">
        <div className="qb-noprint" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span>{user.full_name} · {user.role}</span>
          <button type="button" className="qb-link" onClick={logout}>Log out</button>
        </div>
        <h1>Question bank</h1>
        <p>{data.total} question{data.total === 1 ? "" : "s"}{hasFilters ? " match your filters" : " in total"}</p>
      </header>

      <nav className="qb-tabs qb-noprint" role="tablist" aria-label="Question bank sections">
        <button role="tab" aria-selected={tab === "bank"} onClick={() => setTab("bank")}>Question bank</button>
        <button role="tab" aria-selected={tab === "generate"} onClick={() => setTab("generate")}>Generate paper</button>
        <button role="tab" aria-selected={tab === "papers"} onClick={() => { setFocusPaperId(null); setTab("papers"); }}>Exam papers</button>
      </nav>

      {tab === "generate" && <PaperGenerator onCreated={showPaper} />}
      {tab === "papers" && <PapersView key={focusPaperId || "list"} focusId={focusPaperId} />}

      {tab === "bank" && (<>

      <section
        className={`qb-drop ${dragging ? "is-over" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); upload(e.dataTransfer.files[0]); }}
      >
        <div>
          <strong>Add questions from a file</strong>
          <span>
            Drop a PDF, Excel or CSV here. Every question needs ALL of these: subject, difficulty, topic,
            the question, four options (A to D), the correct answer and a solution. Files with a missing
            column or blank value are rejected.
          </span>
          <span>
            Not sure of the layout? Download a sample:{" "}
            <a className="qb-link" href="/samples/sample_mcq_questions.csv" download>CSV</a> ·{" "}
            <a className="qb-link" href="/samples/sample_mcq_questions.xlsx" download>Excel</a> ·{" "}
            <a className="qb-link" href="/samples/sample_mcq_questions.pdf" download>PDF</a>
          </span>
        </div>
        <input ref={fileRef} type="file" accept=".pdf,.csv,.xlsx" hidden
               onChange={(e) => upload(e.target.files[0])} />
        <button className="qb-btn qb-btn--primary" disabled={uploading}
                onClick={() => fileRef.current?.click()}>
          {uploading ? "Importing…" : "Choose file"}
        </button>
      </section>

      {report && (
        <section className="qb-report" role="status">
          <p>
            <strong>{report.imported} added</strong> from {report.fileName}
            {report.duplicates > 0 && `, ${report.duplicates} skipped as duplicates`}
            {report.errors.length > 0 && `, ${report.errors.length} could not be read`}.
          </p>
          {report.errors.length > 0 && (
            <ul>
              {report.errors.slice(0, 8).map((e, i) => <li key={i}>Row {e.row}: {e.reason}</li>)}
              {report.errors.length > 8 && <li>…and {report.errors.length - 8} more</li>}
            </ul>
          )}
          <button className="qb-link" onClick={() => setReport(null)}>Dismiss</button>
        </section>
      )}
      {rejected && (
        <section className="qb-error" role="alert">
          <p><strong>{rejected.fileName} was not imported.</strong> {rejected.message}</p>
          <ul>
            {rejected.errors.slice(0, 8).map((e, i) => <li key={i}>Row {e.row}: {e.reason}</li>)}
            {rejected.total > 8 && <li>…and {rejected.total - 8} more problem{rejected.total - 8 === 1 ? "" : "s"}</li>}
          </ul>
          <p>
            Use a sample as a guide:{" "}
            <a className="qb-link" href="/samples/sample_mcq_questions.csv" download>CSV</a> ·{" "}
            <a className="qb-link" href="/samples/sample_mcq_questions.xlsx" download>Excel</a> ·{" "}
            <a className="qb-link" href="/samples/sample_mcq_questions.pdf" download>PDF</a>{" "}
            <button className="qb-link" onClick={() => setRejected(null)}>Dismiss</button>
          </p>
        </section>
      )}
      {notice && <p className="qb-report" role="status">{notice}</p>}
      {error && <p className="qb-error" role="alert">{error}</p>}

      <div className="qb-body">
        <aside className="qb-filters" aria-label="Filters">
          <label>Search questions
            <input type="search" value={search} placeholder="e.g. velocity"
                   onChange={(e) => setSearch(e.target.value)} />
          </label>
          <label>Subject
            <select value={filters.subject} onChange={(e) => setFilter("subject", e.target.value)}>
              <option value="">All subjects</option>
              {options.subjects.map((s) => <option key={s}>{s}</option>)}
            </select>
          </label>
          <label>Topic
            <select value={filters.topic} onChange={(e) => setFilter("topic", e.target.value)}>
              <option value="">{filters.subject ? `All ${filters.subject} topics` : "All topics"}</option>
              {options.topics.map((t) => <option key={t}>{t}</option>)}
            </select>
          </label>
          <fieldset>
            <legend>Difficulty</legend>
            <div className="qb-seg">
              {["", "easy", "medium", "hard"].map((d) => (
                <button key={d || "all"} type="button" aria-pressed={filters.difficulty === d}
                        onClick={() => setFilter("difficulty", d)}>
                  {d ? d[0].toUpperCase() + d.slice(1) : "All"}
                </button>
              ))}
            </div>
          </fieldset>
          {hasFilters && <button className="qb-link" onClick={clearAll}>Clear all filters</button>}
        </aside>

        <main className="qb-results">
          <div className="qb-noprint" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", margin: "0 0 10px" }}>
            <span>{data.total} question{data.total === 1 ? "" : "s"}{hasFilters ? " match your filters" : ""}</span>
            <button type="button" className="qb-btn qb-link--danger" disabled={deleting || data.total === 0}
                    onClick={() => bulkDelete(true)}>
              {deleting ? "Deleting…" : hasFilters ? `Delete all ${data.total} matching` : `Delete all ${data.total}`}
            </button>
          </div>
          {(offerSelectAll || allMatching) && (
            <div className="qb-selectall qb-noprint" role="status">
              {allMatching ? (
                <>All <strong>{data.total}</strong> question{data.total === 1 ? "" : "s"}{hasFilters ? " matching your filters" : ""} are selected.{" "}
                  <button className="qb-link" onClick={clearSelection}>Clear selection</button></>
              ) : (
                <>All {data.items.length} questions on this page are selected.{" "}
                  <button className="qb-link" onClick={() => setAllMatching(true)}>
                    Select all {data.total} question{data.total === 1 ? "" : "s"}{hasFilters ? " matching your filters" : ""}
                  </button></>
              )}
            </div>
          )}
          <div className="qb-table-wrap">
            <table>
              <thead>
                <tr><th className="qb-selcol"><input type="checkbox" aria-label="Select all questions on this page" checked={allOnPage} onChange={togglePage} /></th><th>Subject</th><th>Difficulty</th><th>Topic</th><th>Question</th><th><span className="sr">Actions</span></th></tr>
              </thead>
              <tbody>
                {data.items.map((r) => (
                  <tr key={r.id}>
                    <td className="qb-selcol"><input type="checkbox" aria-label={`Select question ${r.id}`} checked={isTicked(r)} onChange={() => toggleRow(r)} /></td>
                    <td>{r.subject}</td>
                    <td><span className={`qb-chip qb-chip--${r.difficulty}`}>{r.difficulty}</span></td>
                    <td>{r.topic}</td>
                    <td className="qb-q">{r.question}<McqBlock q={r} showAnswer /></td>
                    <td><button className="qb-link qb-link--danger" onClick={() => remove(r)}>Delete</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!loading && data.items.length === 0 && (
              <div className="qb-empty">
                {hasFilters
                  ? <>No questions match these filters. <button className="qb-link" onClick={clearAll}>Clear filters</button></>
                  : "Your question bank is empty. Upload a file above to add questions."}
              </div>
            )}
            {loading && <div className="qb-empty">Loading questions…</div>}
          </div>

          {pages > 1 && (
            <nav className="qb-pager" aria-label="Pagination">
              <button className="qb-btn" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
              <span>Page {page} of {pages}</span>
              <button className="qb-btn" disabled={page >= pages} onClick={() => setPage(page + 1)}>Next</button>
            </nav>
          )}
        </main>
      </div>

      {selectedCount > 0 && (
        <div className="qb-basket" role="region" aria-label="Selected questions">
          <span><strong>{selectedCount}</strong> question{selectedCount === 1 ? "" : "s"} selected</span>
          {allMatching && <span>(all pages)</span>}
          <button className="qb-link" onClick={clearSelection}>Clear</button>
          <button className="qb-btn qb-link--danger" disabled={deleting} onClick={deleteSelected}>
            {deleting ? "Deleting…" : `Delete ${allMatching ? "all " : ""}${selectedCount}`}
          </button>
          {!allMatching && (
            <button className="qb-btn qb-btn--primary"
                    onClick={() => setDraft(Object.values(basket).map((q) => ({ question: q, marks: 1 })))}>
              Create exam paper
            </button>
          )}
        </div>
      )}
      </>)}
    </div>
  );
}

/* Lumen Engine — Skill Detail page */
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, type Skill, type CreateExecution, type Execution } from "../api/client";

export default function SkillDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [skill, setSkill] = useState<Skill | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [executionInput, setExecutionInput] = useState("");
  const [lastExecution, setLastExecution] = useState<Execution | null>(null);
  const [executionHistory, setExecutionHistory] = useState<Execution[]>([]);

  useEffect(() => {
    if (!id) return;
    loadSkill();
    loadExecutionHistory();
  }, [id]);

  async function loadSkill() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getSkill(id!);
      setSkill(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load skill");
    } finally {
      setLoading(false);
    }
  }

  async function loadExecutionHistory() {
    if (!id) return;
    try {
      const data = await api.listExecutions(id!, { per_page: 10 });
      setExecutionHistory(data.items);
      if (data.items.length > 0) {
        setLastExecution(data.items[0]);
      }
    } catch (err) {
      console.warn("Failed to load execution history:", err);
    }
  }

  async function handleDelete() {
    if (!confirm("Delete this skill? This cannot be undone.")) return;
    setDeleting(true);
    try {
      await api.deleteSkill(id!);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete");
    } finally {
      setDeleting(false);
    }
  }

  async function handleExecute(e: React.FormEvent) {
    e.preventDefault();
    if (!id) return;
    setExecuting(true);
    setError(null);
    try {
      const execution = await api.executeSkill(id, {
        input_data: executionInput || null,
      });
      setLastExecution(execution);
      setExecutionHistory((prev) => [execution, ...prev.slice(0, 9)]);
      setExecutionInput("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Execution failed");
    } finally {
      setExecuting(false);
    }
  }

  function formatStatus(status: string) {
    const colors: Record<string, string> = {
      completed: "status-completed",
      failed: "status-failed",
      timeout: "status-timeout",
      pending: "status-pending",
      running: "status-running",
    };
    return (
      <span className={`status-badge ${colors[status] || ""}`}>
        {status.toUpperCase()}
      </span>
    );
  }

  if (loading) {
    return <div className="loading">Loading skill...</div>;
  }

  if (error) {
    return <div className="error-banner">{error}</div>;
  }

  if (!skill) {
    return <div className="empty-state">Skill not found.</div>;
  }

  return (
    <div className="skill-detail">
      <h2>{skill.name}</h2>
      <div className="skill-meta">
        <span className="badge">{skill.harness}</span>
        {skill.category && <span className="badge">{skill.category}</span>}
        <span>Version {skill.version}</span>
        <span>Active: {skill.is_active ? "Yes" : "No"}</span>
      </div>

      {skill.description && (
        <p className="skill-description">{skill.description}</p>
      )}

      <div className="skill-commands">
        <h3>Command</h3>
        <pre>{skill.command}</pre>
      </div>

      {skill.tags && skill.tags.length > 0 && (
        <div className="skill-tags">
          <h3>Tags</h3>
          <div className="tags">
            {skill.tags.map((tag) => (
              <span key={tag} className="tag">
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="skill-execution">
        <h3>Execute Skill</h3>
        <form onSubmit={handleExecute} className="execution-form">
          <div className="form-group">
            <label htmlFor="execution-input">Input Data (optional)</label>
            <textarea
              id="execution-input"
              value={executionInput}
              onChange={(e) => setExecutionInput(e.target.value)}
              placeholder="Enter input data for the skill..."
              rows={4}
              disabled={executing}
            />
          </div>
          <button type="submit" disabled={executing || !skill.is_active} className="execute-btn">
            {executing ? "Executing..." : "Execute"}
          </button>
          {!skill.is_active && <span className="inactive-notice">Skill is inactive</span>}
        </form>

        {lastExecution && (
          <div className="execution-result">
            <h4>Last Execution</h4>
            <div className="result-header">
              {formatStatus(lastExecution.status)}
              <span className="result-meta">
                {lastExecution.duration_ms !== null && (
                  <span>Duration: {lastExecution.duration_ms}ms</span>
                )}
                {lastExecution.exit_code !== null && (
                  <span>Exit code: {lastExecution.exit_code}</span>
                )}
              </span>
            </div>
            {lastExecution.output_data && (
              <div className="result-output">
                <strong>Output:</strong>
                <pre>{lastExecution.output_data}</pre>
              </div>
            )}
            {lastExecution.error_message && (
              <div className="result-error">
                <strong>Error:</strong>
                <pre>{lastExecution.error_message}</pre>
              </div>
            )}
            {lastExecution.input_data && (
              <div className="result-input">
                <strong>Input:</strong>
                <pre>{lastExecution.input_data}</pre>
              </div>
            )}
            <small>Executed at: {new Date(lastExecution.created_at).toLocaleString()}</small>
          </div>
        )}

        {executionHistory.length > 1 && (
          <details className="execution-history">
            <summary>Execution History ({executionHistory.length})</summary>
            <ul>
              {executionHistory.map((exec) => (
                <li key={exec.id} className={`history-item ${exec.status}`}>
                  <span className="history-status">{exec.status.toUpperCase()}</span>
                  <span className="history-time">
                    {new Date(exec.created_at).toLocaleString()}
                  </span>
                  {exec.duration_ms !== null && (
                    <span className="history-duration">{exec.duration_ms}ms</span>
                  )}
                  {exec.exit_code !== null && (
                    <span className="history-exit">exit {exec.exit_code}</span>
                  )}
                </li>
              ))}
            </ul>
          </details>
        )}
      </div>

      <div className="skill-timestamps">
        <small>Created: {new Date(skill.created_at).toLocaleString()}</small>
        <small>Updated: {new Date(skill.updated_at).toLocaleString()}</small>
      </div>

      <div className="detail-actions">
        <button onClick={() => navigate("/")}>Back to Catalog</button>
        <button
          onClick={handleDelete}
          disabled={deleting}
          className="danger-btn"
        >
          {deleting ? "Deleting..." : "Delete Skill"}
        </button>
      </div>
    </div>
  );
}

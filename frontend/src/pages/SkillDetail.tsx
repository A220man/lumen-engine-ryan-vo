/* Lumen Engine — Skill Detail page */
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { api, type Skill } from "../api/client";

export default function SkillDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [skill, setSkill] = useState<Skill | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    if (!id) return;
    loadSkill();
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
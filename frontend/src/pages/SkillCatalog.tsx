/* Lumen Engine — Skill Catalog Page */
import { useEffect, useState } from "react";
import { api, type Skill, type CreateSkill } from "../api/client";
import SkillList from "../components/SkillList";

export default function SkillCatalog() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [harnessFilter, setHarnessFilter] = useState<string>("");
  const [showForm, setShowForm] = useState(false);
  const [newSkill, setNewSkill] = useState<CreateSkill>({
    name: "",
    harness: "generic",
    command: "",
    tags: [],
    version: "1.0.0",
  });

  const fetchSkills = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, unknown> = { page, per_page: perPage };
      if (search) params.search = search;
      if (harnessFilter) params.harness = harnessFilter;
      const data = await api.listSkills(params);
      setSkills(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load skills");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSkills();
  }, [page, search, harnessFilter]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.createSkill(newSkill);
      setShowForm(false);
      setNewSkill({
        name: "",
        harness: "generic",
        command: "",
        tags: [],
        version: "1.0.0",
      });
      fetchSkills();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create skill");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this skill?")) return;
    try {
      await api.deleteSkill(id);
      fetchSkills();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete skill");
    }
  };

  const pages = Math.ceil(total / perPage);

  return (
    <div className="skill-catalog">
      <div className="toolbar">
        <input
          type="text"
          placeholder="Search skills..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="search-input"
        />
        <select
          value={harnessFilter}
          onChange={(e) => setHarnessFilter(e.target.value)}
        >
          <option value="">All Harnesses</option>
          <option value="claude-code">Claude Code</option>
          <option value="codex">Codex</option>
          <option value="opencode">OpenCode</option>
          <option value="cursor">Cursor</option>
          <option value="generic">Generic</option>
        </select>
        <button
          onClick={() => setShowForm(!showForm)}
          className="primary-btn"
        >
          {showForm ? "Cancel" : "+ New Skill"}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleCreate} className="skill-form">
          <h3>Define New Skill</h3>
          <input
            type="text"
            placeholder="Name"
            value={newSkill.name}
            onChange={(e) =>
              setNewSkill({ ...newSkill, name: e.target.value })
            }
            required
            maxLength={200}
          />
          <input
            type="text"
            placeholder="Command (e.g. cat @selection | lumen explain)"
            value={newSkill.command}
            onChange={(e) =>
              setNewSkill({ ...newSkill, command: e.target.value })
            }
            required
            maxLength={5000}
          />
          <input
            type="text"
            placeholder="Harness (e.g. claude-code)"
            value={newSkill.harness}
            onChange={(e) =>
              setNewSkill({ ...newSkill, harness: e.target.value })
            }
            defaultValue="generic"
          />
          <input
            type="text"
            placeholder="Category (optional)"
            value={newSkill.category || ""}
            onChange={(e) =>
              setNewSkill({ ...newSkill, category: e.target.value || null })
            }
          />
          <input
            type="text"
            placeholder="Tags (comma-separated)"
            value={(newSkill.tags || []).join(", ")}
            onChange={(e) =>
              setNewSkill({
                ...newSkill,
                tags: e.target.value
                  .split(",")
                  .map((t) => t.trim())
                  .filter(Boolean),
              })
            }
          />
          <input
            type="text"
            placeholder="Version"
            value={newSkill.version || "1.0.0"}
            onChange={(e) =>
              setNewSkill({ ...newSkill, version: e.target.value })
            }
            defaultValue="1.0.0"
          />
          <textarea
            placeholder="Description (optional)"
            value={newSkill.description || ""}
            onChange={(e) =>
              setNewSkill({ ...newSkill, description: e.target.value || null })
            }
            rows={3}
          />
          <div className="form-actions">
            <button type="submit" className="primary-btn">
              Save Skill
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {error && <div className="error-banner">{error}</div>}

      <SkillList
        skills={skills}
        loading={loading}
        total={total}
        page={page}
        pages={pages}
        onPageChange={setPage}
        onDelete={handleDelete}
      />
    </div>
  );
}
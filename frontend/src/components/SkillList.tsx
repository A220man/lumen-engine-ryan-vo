/* Lumen Engine — Skill List and Detail components */
import { api, type Skill } from "../api/client";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

interface SkillListProps {
  skills: Skill[];
  loading: boolean;
  total: number;
  page: number;
  pages: number;
  onPageChange: (page: number) => void;
  onDelete: (id: string) => void;
}

export default function SkillList({
  skills,
  loading,
  total,
  page,
  pages,
  onPageChange,
  onDelete,
}: SkillListProps) {
  if (loading) {
    return <div className="loading">Loading skills...</div>;
  }

  if (total === 0) {
    return (
      <div className="empty-state">
        <p>No skills found. Create one to get started.</p>
      </div>
    );
  }

  return (
    <div className="skill-list">
      <p className="results-count">
        {total} skill{total !== 1 ? "s" : ""} (page {page} of {pages || 1})
      </p>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Harness</th>
            <th>Category</th>
            <th>Tags</th>
            <th>Active</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {skills.map((skill) => (
            <tr key={skill.id}>
              <td>
                <Link to={`/skills/${skill.id}`}>{skill.name}</Link>
              </td>
              <td>{skill.harness}</td>
              <td>{skill.category || "-"}</td>
              <td>{(skill.tags || []).join(", ")}</td>
              <td>{skill.is_active ? "✓" : "✗"}</td>
              <td>
                <button
                  onClick={() => onDelete(skill.id)}
                  className="danger-btn"
                >
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {pages > 1 && (
        <div className="pagination">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
          >
            Previous
          </button>
          <span>
            Page {page} of {pages}
          </span>
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= pages}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
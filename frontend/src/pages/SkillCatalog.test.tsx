import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import SkillCatalog from "./SkillCatalog";
import { api } from "../api/client";
import type { PaginatedSkills } from "../api/client";

vi.mock("../api/client", () => ({
  api: {
    health: vi.fn(),
    listSkills: vi.fn(),
    getSkill: vi.fn(),
    createSkill: vi.fn(),
    updateSkill: vi.fn(),
    deleteSkill: vi.fn(),
  },
  // Types are erased at runtime
}));
vi.mock("react-router-dom", () => ({
  useNavigate: () => vi.fn(),
  useParams: () => ({ id: "test-id" }),
  BrowserRouter: ({ children }: { children: React.ReactNode }) =>
    children as React.ReactElement,
  Routes: ({ children }: { children: React.ReactNode }) =>
    children as React.ReactElement,
  Route: ({ element }: { element: React.ReactNode }) =>
    element as React.ReactElement,
  Link: ({ children }: { children: React.ReactNode; to: string }) =>
    (children as React.ReactElement),
  useLocation: () => ({ pathname: "/" }),
}));

const mockSkills = [
  {
    id: "123e4567-e89b-12d3-a456-426614174000",
    name: "explain-code",
    description: "Explains selected code",
    harness: "claude-code",
    command: "cat @selection | python3 -m lumen.explain",
    category: "documentation",
    tags: ["explanation"],
    is_active: true,
    version: "1.0.0",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  },
];

describe("SkillCatalog", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.listSkills).mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      per_page: 20,
      pages: 0,
    });
  });

  it("shows empty state when no skills exist", async () => {
    render(<SkillCatalog />);

    await waitFor(() => {
      expect(screen.getByText(/No skills found/i)).toBeInTheDocument();
    });
  });

  it("displays skills in the list after loading", async () => {
    vi.mocked(api.listSkills).mockResolvedValue({
      items: mockSkills,
      total: 1,
      page: 1,
      per_page: 20,
      pages: 1,
    });

    render(<SkillCatalog />);

    await waitFor(() => {
      expect(screen.getByText("explain-code")).toBeInTheDocument();
    });
    expect(screen.getByText("claude-code")).toBeInTheDocument();
    expect(
      screen.getByText("1 skill (page 1 of 1)")
    ).toBeInTheDocument();
  });

  it("shows loading state while fetching skills", async () => {
    const { promise } = Promise.withResolvers<PaginatedSkills>();
    vi.mocked(api.listSkills).mockReturnValue(promise);

    render(<SkillCatalog />);

    expect(screen.getByText(/Loading skills/i)).toBeInTheDocument();
  });
});
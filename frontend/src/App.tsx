/* Lumen Engine — Agent Harness Performance Optimization System */
import { Routes, Route, Link, useLocation } from "react-router-dom";
import SkillCatalog from "./pages/SkillCatalog";
import SkillDetail from "./pages/SkillDetail";

export default function App() {
  const location = useLocation();
  return (
    <div className="app">
      <header className="app-header">
        <h1>Lumen Engine</h1>
        <nav>
          <Link
            to="/"
            className={location.pathname === "/" ? "active" : ""}
          >
            Skill Catalog
          </Link>
        </nav>
      </header>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<SkillCatalog />} />
          <Route path="/skills/:id" element={<SkillDetail />} />
        </Routes>
      </main>
    </div>
  );
}
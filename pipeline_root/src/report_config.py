"""
HTML report configuration for S5 renderer.
Colors, severity ordering, and CSS live here
so S5_renderer.py stays focused on structure.
"""

SEVERITY_ORDER = [
    "CRITICAL", "MAJOR", "MINOR", "INFO",
]

SEVERITY_COLOR = {
    "CRITICAL": "#dc2626",
    "MAJOR":    "#d97706",
    "MINOR":    "#ca8a04",
    "INFO":     "#2563eb",
}

TYPE_COLOR = {
    "FINDING":     "#374151",
    "QUESTION":    "#7c3aed",
    "OBSERVATION": "#6b7280",
}

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: system-ui, -apple-system, sans-serif;
  font-size: 14px;
  line-height: 1.5;
  color: #1f2937;
  background: #f9fafb;
  padding: 2rem;
  max-width: 960px;
  margin: 0 auto;
}
h1 { font-size: 1.5rem; margin-bottom: 0.5rem; }
h2 {
  font-size: 1.1rem;
  margin: 1.5rem 0 0.75rem;
  color: #374151;
}

/* meta */
header { margin-bottom: 2rem; }
.meta-grid {
  display: grid;
  grid-template-columns: 9rem 1fr;
  gap: 0.2rem 0.75rem;
}
.meta-grid dt { font-weight: 600; color: #6b7280; }

/* dashboard */
#dashboard {
  background: #fff;
  border-radius: 8px;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  color: #1f2937;
}
.total-count {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
}
.stat-row {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}
.stat-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  background: #f3f4f6;
  min-width: 80px;
}
.stat-cell .count {
  font-size: 1.5rem;
  font-weight: 700;
  line-height: 1;
}
.stat-cell .label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #6b7280;
  margin-top: 2px;
}
.sev-critical { background: #fef2f2; color: #dc2626; }
.sev-major    { background: #fffbeb; color: #d97706; }
.sev-minor    { background: #fefce8; color: #ca8a04; }
.sev-info     { background: #eff6ff; color: #2563eb; }

/* flags */
.flag-card {
  background: #fff;
  border-left: 4px solid #e5e7eb;
  border-radius: 0 6px 6px 0;
  padding: 1rem 1.25rem;
  margin-bottom: 0.75rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  color: #4A4A4A;
}
.flag-card.sev-critical { border-left-color: #dc2626; }
.flag-card.sev-major    { border-left-color: #d97706; }
.flag-card.sev-minor    { border-left-color: #ca8a04; }
.flag-card.sev-info     { border-left-color: #2563eb; }

.flag-header {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
}
.flag-id {
  font-family: monospace;
  font-size: 0.8rem;
  color: #6b7280;
}
.badge {
  font-size: 0.7rem;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.sev-badge { color: #fff; }
.type-badge, .cat-badge { background: #f3f4f6; }
.confidence {
  font-size: 0.75rem;
  color: #9ca3af;
  margin-left: auto;
}
.affected-items {
  font-size: 0.85rem;
  margin-bottom: 0.4rem;
}
.description { margin-bottom: 0.5rem; }
.recommendation {
  font-size: 0.9rem;
  background: #f0fdf4;
  border-left: 3px solid #22c55e;
  padding: 0.5rem 0.75rem;
  border-radius: 0 4px 4px 0;
  margin-bottom: 0.4rem;
}
.reference { font-size: 0.8rem; color: #6b7280; }
"""

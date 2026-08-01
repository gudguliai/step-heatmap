import React, { useEffect, useMemo, useState } from "react";

const GREEN = 10000; // 10K+ steps
const YELLOW = 5000; // more than 5K

function level(steps) {
  if (steps === null || steps === undefined) return "empty";
  if (steps >= GREEN) return "green";
  if (steps > YELLOW) return "yellow";
  return "red";
}

const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];
const DAY_LABELS = ["", "Mon", "", "Wed", "", "Fri", ""];

function parseDay(day) {
  const [y, m, d] = day.date.split("-").map(Number);
  return new Date(y, m - 1, d);
}

/** Build weeks (columns) of 7 day-cells starting Sunday, from firstData to today. */
function buildWeeks(days) {
  const byDate = new Map();
  for (const day of days) byDate.set(day.date, day.steps);

  const start = days.length ? parseDay(days[0]) : new Date();
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const weeks = [];
  let weekStart = new Date(start);
  weekStart.setDate(weekStart.getDate() - weekStart.getDay()); // back to Sunday

  while (weekStart <= today) {
    const cells = [];
    for (let i = 0; i < 7; i++) {
      const d = new Date(weekStart);
      d.setDate(weekStart.getDate() + i);
      const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
      const inRange = d >= start && d <= today;
      const steps = byDate.has(key) ? byDate.get(key) : null;
      cells.push({ date: key, steps, inRange });
    }
    weeks.push({ cells, monthLabel: monthLabelFor(weekStart, weeks.length) });
    weekStart.setDate(weekStart.getDate() + 7);
  }
  return weeks;
}

function monthLabelFor(weekStart, index) {
  if (index === 0) return MONTHS[weekStart.getMonth()];
  const prev = new Date(weekStart);
  prev.setDate(prev.getDate() - 7);
  return prev.getMonth() !== weekStart.getMonth() ? MONTHS[weekStart.getMonth()] : null;
}

function Tooltip({ day, visible, x, y }) {
  if (!visible || !day) return null;
  const label =
    day.steps === null || day.steps === undefined
      ? "No data"
      : `${day.steps.toLocaleString()} steps`;
  return (
    <div className="tooltip" style={{ left: x, top: y }}>
      <strong>{day.date}</strong>
      <span>{label}</span>
    </div>
  );
}

export default function App() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [tip, setTip] = useState(null); // {day, x, y}

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}steps.json`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((j) => setData(j))
      .catch((e) => setError(String(e)));
  }, []);

  const weeks = useMemo(() => (data ? buildWeeks(data.days || []) : []), [data]);

  if (error) {
    return (
      <main className="card">
        <h1>Step Heatmap</h1>
        <p className="error">Could not load steps.json: {error}</p>
      </main>
    );
  }

  if (!data) {
    return (
      <main className="card">
        <h1>Step Heatmap</h1>
        <p className="muted">Loading…</p>
      </main>
    );
  }

  const total = (data.days || []).reduce((s, d) => s + (d.steps || 0), 0);
  const avg = (data.days || []).length
    ? Math.round(total / (data.days || []).length)
    : 0;

  return (
    <main className="card">
      <header>
        <h1>Step Heatmap</h1>
        <p className="muted">
          {data.days?.length || 0} days · avg {avg.toLocaleString()} steps/day
          {data.updated ? ` · updated ${new Date(data.updated).toLocaleDateString()}` : ""}
        </p>
      </header>

      <div className="heatmap-wrap">
        <div className="heatmap">
          <div className="months">
            {weeks.map((w, i) => (
              <span key={i} className="month-label" style={{ gridColumn: i + 1 }}>
                {w.monthLabel || ""}
              </span>
            ))}
          </div>
          <div className="grid">
            {weeks.map((w, wi) => (
              <div className="week" key={wi} style={{ gridColumn: wi + 1 }}>
                {w.cells.map((cell, ci) => (
                  <div
                    key={cell.date}
                    className={`cell ${level(cell.steps)}${cell.inRange ? "" : " out"}`}
                    onMouseEnter={(e) => {
                      const r = e.currentTarget.getBoundingClientRect();
                      setTip({ day: cell, x: r.left, y: r.top });
                    }}
                    onMouseLeave={() => setTip(null)}
                    onClick={() => setTip({ day: cell, x: 8, y: 90 })}
                  />
                ))}
              </div>
            ))}
          </div>
          <div className="days">
            {DAY_LABELS.map((l, i) => (
              <span key={i}>{l}</span>
            ))}
          </div>
        </div>
      </div>

      <footer className="legend">
        <span className="muted">Less</span>
        <span className="cell red" />
        <span className="cell yellow" />
        <span className="cell green" />
        <span className="muted">More</span>
        <span className="legend-text">green ≥10K · yellow &gt;5K · red &lt;5K</span>
      </footer>

      {tip && (
        <Tooltip
          day={tip.day}
          visible
          x={tip.x}
          y={tip.y}
        />
      )}
    </main>
  );
}

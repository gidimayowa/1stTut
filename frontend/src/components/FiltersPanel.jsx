import React from 'react'

export default function FiltersPanel({ filters, setFilters, studies, conditions, tasks }) {
  const onChange = (key, value) => setFilters((prev) => ({ ...prev, [key]: value }))
  return (
    <div style={{ display: 'grid', gap: 8 }}>
      <label>Study
        <select value={filters.study_id} onChange={(e) => onChange('study_id', e.target.value)}>
          <option value="">All</option>
          {studies.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </label>
      <label>Condition
        <select value={filters.condition_id} onChange={(e) => onChange('condition_id', e.target.value)}>
          <option value="">All</option>
          {conditions.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </label>
      <label>Task
        <select value={filters.task_id} onChange={(e) => onChange('task_id', e.target.value)}>
          <option value="">All</option>
          {tasks.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
      </label>
      <label>Start date<input type="date" value={filters.start_date} onChange={(e) => onChange('start_date', e.target.value)} /></label>
      <label>End date<input type="date" value={filters.end_date} onChange={(e) => onChange('end_date', e.target.value)} /></label>
      <label><input type="checkbox" checked={filters.anomalies_only} onChange={(e) => onChange('anomalies_only', e.target.checked)} /> Show anomalies only</label>
    </div>
  )
}

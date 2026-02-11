import React from 'react'

export default function KPIStrip({ summary }) {
  const items = [
    ['Participants', summary.participants ?? 0],
    ['Sessions', summary.sessions ?? 0],
    ['Mean completion (s)', Number(summary.mean_completion_time || 0).toFixed(2)],
    ['Median completion (s)', Number(summary.median_completion_time || 0).toFixed(2)],
    ['Mean errors', Number(summary.mean_errors || 0).toFixed(2)],
    ['Last ingest', summary.last_ingest_timestamp || '—'],
  ]

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, minmax(100px, 1fr))', gap: 10 }}>
      {items.map(([k, v]) => (
        <div key={k} style={{ background: '#fff', borderRadius: 10, padding: 12, boxShadow: '0 1px 4px rgba(0,0,0,0.08)' }}>
          <div style={{ fontSize: 12, color: '#666' }}>{k}</div>
          <div style={{ fontWeight: 700 }}>{v}</div>
        </div>
      ))}
    </div>
  )
}

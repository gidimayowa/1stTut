import React from 'react'

export default function Card({ title, children, actions }) {
  return (
    <section style={{ background: '#fff', borderRadius: 12, padding: 16, boxShadow: '0 1px 6px rgba(0,0,0,0.08)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <h3 style={{ margin: 0, fontSize: 18 }}>{title}</h3>
        {actions}
      </div>
      {children}
    </section>
  )
}

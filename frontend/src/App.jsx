import React, { useMemo } from 'react'
import Plot from 'react-plotly.js'

const mock = [
  { condition: 'control', completion: 180, errors: 4, sessionNo: 1 },
  { condition: 'ar_guided', completion: 150, errors: 2, sessionNo: 1 },
  { condition: 'control', completion: 160, errors: 3, sessionNo: 2 },
  { condition: 'ar_guided', completion: 130, errors: 2, sessionNo: 2 },
]

export default function App() {
  const byCondition = useMemo(() => {
    const keys = [...new Set(mock.map((x) => x.condition))]
    return keys.map((k) => ({
      type: 'box',
      name: k,
      y: mock.filter((x) => x.condition === k).map((x) => x.completion),
      boxpoints: 'all'
    }))
  }, [])

  return (
    <main style={{ fontFamily: 'sans-serif', margin: 24 }}>
      <h1>GDPR-aware XR Research Platform</h1>
      <p>Upload sessions, compute metrics, run analyses, and export publication-ready reports.</p>
      <section>
        <h2>Completion time by condition</h2>
        <Plot data={byCondition} layout={{ width: 700, height: 360, yaxis: { title: 'Seconds' } }} />
      </section>
      <section>
        <h2>Learning curve</h2>
        <Plot
          data={[
            {
              type: 'scatter',
              mode: 'lines+markers',
              x: mock.map((x) => x.sessionNo),
              y: mock.map((x) => x.completion),
              text: mock.map((x) => x.condition),
            },
          ]}
          layout={{ width: 700, height: 360, xaxis: { title: 'Session #' }, yaxis: { title: 'Completion time' } }}
        />
      </section>
    </main>
  )
}

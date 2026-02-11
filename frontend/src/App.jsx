import React, { useEffect, useMemo, useState } from 'react'
import Plot from 'react-plotly.js'

import { api, API_BASE } from './api'
import Card from './components/Card'
import FiltersPanel from './components/FiltersPanel'
import KPIStrip from './components/KPIStrip'

const initialFilters = {
  study_id: '',
  condition_id: '',
  task_id: '',
  start_date: '',
  end_date: '',
  anomalies_only: false,
}

function paramsFromFilters(filters) {
  const p = {}
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== '' && v !== false && v != null) p[k] = v
  })
  return p
}

export default function App() {
  const [filters, setFilters] = useState(initialFilters)
  const [summary, setSummary] = useState({})
  const [sessions, setSessions] = useState([])
  const [events, setEvents] = useState([])
  const [selectedSession, setSelectedSession] = useState(null)
  const [studies, setStudies] = useState([])
  const [conditions, setConditions] = useState([])
  const [tasks, setTasks] = useState([])
  const [analysisRuns, setAnalysisRuns] = useState([])
  const [analysisResult, setAnalysisResult] = useState(null)
  const [exclusions, setExclusions] = useState([{ rule_name: 'exclude_duration_lt', params: { seconds: 30 } }])
  const [analysisForm, setAnalysisForm] = useState({ dependent_variable: 'task_completion_time_sec', group_variable: 'condition_id', test_type: 'auto', auto_normality: true })
  const [uploadState, setUploadState] = useState({ study_id: '', condition_id: '', task_id: '', files: [], results: [] })
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [reportLink, setReportLink] = useState('')

  const refresh = async () => {
    try {
      setBusy(true)
      setError('')
      const filterParams = paramsFromFilters(filters)
      const [summaryRes, sessionRes, studiesRes] = await Promise.all([
        api.get('/api/summary', { params: filterParams }),
        api.get('/api/sessions', { params: filterParams }),
        api.get('/api/studies'),
      ])
      setSummary(summaryRes.data)
      setSessions(sessionRes.data)
      setStudies(studiesRes.data)
      if (filters.study_id) {
        const [condRes, taskRes] = await Promise.all([
          api.get('/api/conditions', { params: { study_id: filters.study_id } }),
          api.get('/api/tasks', { params: { study_id: filters.study_id } }),
        ])
        setConditions(condRes.data)
        setTasks(taskRes.data)
        const runs = await api.get('/api/analysis/runs', { params: { study_id: filters.study_id } })
        setAnalysisRuns(runs.data)
      }
    } catch (e) {
      setError(e?.response?.data?.detail || e.message)
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => { refresh() }, [filters])

  useEffect(() => {
    const qp = new URLSearchParams(window.location.search)
    setFilters((prev) => ({ ...prev, ...Object.fromEntries(qp.entries()), anomalies_only: qp.get('anomalies_only') === 'true' }))
  }, [])

  useEffect(() => {
    const qp = new URLSearchParams(paramsFromFilters(filters))
    window.history.replaceState({}, '', `${window.location.pathname}?${qp.toString()}`)
  }, [filters])

  const uploadAndIngest = async () => {
    if (!uploadState.study_id || !uploadState.condition_id || uploadState.files.length === 0) return
    const fd = new FormData()
    fd.append('study_id', uploadState.study_id)
    fd.append('condition_id', uploadState.condition_id)
    if (uploadState.task_id) fd.append('task_id', uploadState.task_id)
    uploadState.files.forEach((f) => fd.append('files', f))
    const ingestRes = await api.post('/api/ingest', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    setUploadState((prev) => ({ ...prev, results: ingestRes.data.results }))
    await api.post('/api/metrics/recompute', new URLSearchParams({ study_id: uploadState.study_id }))
    setFilters((prev) => ({ ...prev, study_id: uploadState.study_id }))
    await refresh()
  }

  const runAnalysis = async () => {
    const payload = {
      study_id: filters.study_id || uploadState.study_id,
      ...analysisForm,
      exclusions,
    }
    const res = await api.post('/api/analysis/run', payload)
    setAnalysisResult(res.data)
    await refresh()
  }

  const generateReport = async () => {
    if (!analysisResult?.results) return
    const res = await api.post('/api/analysis/report', { run_id: analysisResult.results.run_id, results: analysisResult.results, provenance: analysisResult.provenance })
    setReportLink(`${API_BASE}${res.data.download_url}`)
  }

  const inspectSession = async (sessionId) => {
    setSelectedSession(sessionId)
    const res = await api.get(`/api/sessions/${sessionId}/events`)
    setEvents(res.data)
  }

  const completionBox = useMemo(() => {
    const grouped = sessions.reduce((acc, s) => {
      acc[s.condition_id] = acc[s.condition_id] || []
      acc[s.condition_id].push(s.task_completion_time_sec)
      return acc
    }, {})
    return Object.entries(grouped).map(([k, v]) => ({ type: 'box', name: k, y: v, boxpoints: 'all' }))
  }, [sessions])

  const errorBar = useMemo(() => {
    const grouped = sessions.reduce((acc, s) => {
      acc[s.condition_id] = (acc[s.condition_id] || 0) + s.total_errors
      return acc
    }, {})
    return [{ type: 'bar', x: Object.keys(grouped), y: Object.values(grouped) }]
  }, [sessions])

  return (
    <main style={{ fontFamily: 'Inter, Arial, sans-serif', background: '#f4f6fb', minHeight: '100vh', padding: 18 }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 14 }}>
        <h1 style={{ margin: 0 }}>GDPR-aware XR Research Platform</h1>
        <span style={{ background: '#e8ecff', borderRadius: 8, padding: '6px 10px' }}>Env: local ({API_BASE})</span>
      </header>
      {error && <div style={{ marginBottom: 10, background: '#ffe7e7', padding: 10, borderRadius: 8 }}>{error}</div>}
      {busy && <div style={{ marginBottom: 10 }}>Loading...</div>}
      <KPIStrip summary={summary} />

      <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr', gap: 14, marginTop: 14 }}>
        <Card title="Filters"><FiltersPanel filters={filters} setFilters={setFilters} studies={studies} conditions={conditions} tasks={tasks} /></Card>
        <div style={{ display: 'grid', gap: 14 }}>
          <Card title="Ingest Data">
            <div style={{ display: 'grid', gap: 8 }}>
              <input placeholder="study_id" value={uploadState.study_id} onChange={(e) => setUploadState((p) => ({ ...p, study_id: e.target.value }))} />
              <input placeholder="condition_id" value={uploadState.condition_id} onChange={(e) => setUploadState((p) => ({ ...p, condition_id: e.target.value }))} />
              <input placeholder="task_id (optional)" value={uploadState.task_id} onChange={(e) => setUploadState((p) => ({ ...p, task_id: e.target.value }))} />
              <input type="file" multiple accept=".csv,.jsonl" onChange={(e) => setUploadState((p) => ({ ...p, files: Array.from(e.target.files || []) }))} />
              <button onClick={uploadAndIngest}>Upload & ingest</button>
              {uploadState.results.map((r) => <div key={r.filename}>{r.filename}: {r.status} {r.error ? ` - ${r.error}` : ''}</div>)}
            </div>
          </Card>

          <Card title="Metrics" actions={<button onClick={() => api.post('/api/metrics/recompute', new URLSearchParams({ study_id: filters.study_id || uploadState.study_id })).then(refresh)}>Recompute metrics</button>}>
            Last update: {summary.last_ingest_timestamp || '—'}
          </Card>

          <Card title="Analysis Runner">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 8 }}>
              <select value={analysisForm.dependent_variable} onChange={(e) => setAnalysisForm((p) => ({ ...p, dependent_variable: e.target.value }))}>
                <option value="task_completion_time_sec">completion_time</option>
                <option value="total_errors">error_rate</option>
              </select>
              <select value={analysisForm.group_variable} onChange={(e) => setAnalysisForm((p) => ({ ...p, group_variable: e.target.value }))}>
                <option value="condition_id">condition</option>
                <option value="task_id">task</option>
              </select>
              <select value={analysisForm.test_type} onChange={(e) => setAnalysisForm((p) => ({ ...p, test_type: e.target.value }))}>
                {['auto', 't-test', 'mann-whitney', 'anova', 'kruskal', 'mixed-effects'].map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
              <label><input type="checkbox" checked={analysisForm.auto_normality} onChange={(e) => setAnalysisForm((p) => ({ ...p, auto_normality: e.target.checked }))} /> auto normality</label>
            </div>
            <div style={{ marginTop: 8 }}>
              {exclusions.map((r, i) => (
                <div key={`${r.rule_name}-${i}`} style={{ display: 'flex', gap: 8, marginBottom: 6 }}>
                  <select value={r.rule_name} onChange={(e) => setExclusions((prev) => prev.map((x, idx) => idx === i ? { ...x, rule_name: e.target.value } : x))}>
                    <option value="exclude_duration_lt">duration &lt; X</option>
                    <option value="exclude_missing_timestamp_pct_gt">missing timestamps &gt; Y%</option>
                    <option value="exclude_pretest_score_gt">pretest &gt; threshold</option>
                  </select>
                  <input value={Object.values(r.params)[0]} onChange={(e) => {
                    const key = Object.keys(r.params)[0] || 'seconds'
                    setExclusions((prev) => prev.map((x, idx) => idx === i ? { ...x, params: { [key]: Number(e.target.value) } } : x))
                  }} />
                  <button onClick={() => setExclusions((prev) => prev.filter((_, idx) => idx !== i))}>Remove</button>
                </div>
              ))}
              <button onClick={() => setExclusions((prev) => [...prev, { rule_name: 'exclude_duration_lt', params: { seconds: 30 } }])}>Add rule</button>
            </div>
            <div style={{ marginTop: 10, display: 'flex', gap: 8 }}>
              <button onClick={runAnalysis}>Run analysis</button>
              <button onClick={generateReport}>Generate report</button>
              {reportLink && <a href={reportLink}>Download report</a>}
              {(filters.study_id || uploadState.study_id) && <a href={`${API_BASE}/api/exports/cleaned.csv?study_id=${filters.study_id || uploadState.study_id}`}>Download cleaned CSV</a>}
            </div>
            {analysisResult && <pre style={{ background: '#f8f8f8', padding: 8, borderRadius: 8, marginTop: 10 }}>{JSON.stringify(analysisResult.results, null, 2)}</pre>}
            <div style={{ marginTop: 10 }}><b>Previous runs:</b> {analysisRuns.map((r) => <span key={r.run_id} style={{ marginRight: 8 }}>{r.run_id.slice(0, 8)}</span>)}</div>
          </Card>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
            <Card title="Completion time by condition"><Plot data={completionBox} layout={{ height: 300 }} /></Card>
            <Card title="Error count by condition"><Plot data={errorBar} layout={{ height: 300 }} /></Card>
          </div>

          <Card title="Session Inspector">
            <table width="100%" cellPadding="6">
              <thead><tr><th>participant</th><th>session</th><th>condition</th><th>task</th><th>duration</th><th>completion</th><th>errors</th><th>anomaly</th></tr></thead>
              <tbody>
                {sessions.map((s) => (
                  <tr key={s.session_id} onClick={() => inspectSession(s.session_id)} style={{ cursor: 'pointer', background: s.session_id === selectedSession ? '#eef3ff' : 'transparent' }}>
                    <td>{s.participant_id}</td><td>{s.session_id}</td><td>{s.condition_id}</td><td>{s.task_id}</td><td>{s.duration_sec}</td><td>{s.task_completion_time_sec}</td><td>{s.total_errors}</td>
                    <td>{s.anomaly_flag ? `⚠ ${s.anomaly_reason}` : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {events.length > 0 && (
              <Plot
                data={[{ type: 'scatter', mode: 'markers', x: events.map((e) => e.time_since_session_start_ms), y: events.map((e) => e.event_type), text: events.map((e) => e.task_id) }]}
                layout={{ height: 300, xaxis: { title: 'ms since start' }, yaxis: { title: 'event type' } }}
              />
            )}
          </Card>
        </div>
      </div>
    </main>
  )
}

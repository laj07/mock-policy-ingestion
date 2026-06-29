import { useState } from "react"

const API = "http://127.0.0.1:8000"

function SlipCard({ slip, onApprove, onReject }) {
  const [lob, setLob] = useState(slip.lob || "")
  const [region, setRegion] = useState(slip.region || "")

  return (
    <div style={styles.card}>
      <div style={styles.cardHeader}>
        <span style={styles.filename}>{slip.filename}</span>
        <span style={{
          ...styles.badge,
          background: slip.status === "auto_approved" ? "#16a34a" :
                      slip.status === "needs_human_review" ? "#d97706" : "#dc2626"
        }}>
          {slip.status}
        </span>
      </div>
      <div style={styles.cardBody}>
        <p><b>Insured:</b> {slip.insured || "—"}</p>
        <p><b>LOB:</b> {slip.lob || "—"}</p>
        <p><b>Region:</b> {slip.region || "—"}</p>
        <p><b>Broker:</b> {slip.broker || "—"}</p>
        <p><b>Premium:</b> {slip.premium || "—"}</p>
        <p><b>Confidence:</b> {slip.confidence}</p>
      </div>

      {slip.status === "needs_human_review" && (
        <div style={{ marginTop: "12px" }}>
          <div style={{ marginBottom: "8px" }}>
            <label style={styles.label}>Correct LOB</label>
            <select value={lob} onChange={e => setLob(e.target.value)} style={styles.select}>
              <option value="">— Select —</option>
              <option value="Marine">Marine</option>
              <option value="Aviation">Aviation</option>
              <option value="Property">Property</option>
              <option value="Liability">Liability</option>
              <option value="Motor">Motor</option>
            </select>
          </div>
          <div style={{ marginBottom: "12px" }}>
            <label style={styles.label}>Correct Region</label>
            <input
              type="text"
              value={region}
              onChange={e => setRegion(e.target.value)}
              placeholder="e.g. Singapore, Canada, Middle East..."
              style={styles.input}
            />
          </div>
          <div style={styles.cardActions}>
            <button
              style={styles.approveBtn}
              onClick={() => onApprove(slip.thread_id, {
                status: "approved",
                corrected_lob: lob,
                corrected_region: region,
                reviewer: "human"
              })}
            >
              Approve
            </button>
            <button style={styles.rejectBtn} onClick={() => onReject(slip.thread_id)}>
              Reject
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default function App() {
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)

  const autoApproved = results.filter(s => s.status === "auto_approved")
  const needsReview = results.filter(s => s.status === "needs_human_review")
  const rejected = results.filter(s => s.status === "rejected")

  async function handlePoll() {
    setLoading(true)
    const res = await fetch(`${API}/poll`, { method: "POST" })
    const data = await res.json()
    setResults(data.results)
    setLoading(false)
  }

  async function handleApprove(threadId, decision) {
    await fetch(`${API}/validate/${threadId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(decision)
    })
    setResults(prev => prev.map(s =>
      s.thread_id === threadId
        ? { ...s, status: "auto_approved", lob: decision.corrected_lob, region: decision.corrected_region }
        : s
    ))
  }

  async function handleReject(threadId) {
    await fetch(`${API}/validate/${threadId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "rejected", reviewer: "human" })
    })
    setResults(prev => prev.map(s =>
      s.thread_id === threadId ? { ...s, status: "rejected" } : s
    ))
  }

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <h1 style={styles.title}>Allianz Policy Ingestion Dashboard</h1>
        <button style={styles.pollBtn} onClick={handlePoll} disabled={loading}>
          {loading ? "Polling..." : "Poll Sources"}
        </button>
      </div>

      <div style={styles.columns}>
        <div style={styles.column}>
          <h2 style={{ color: "#16a34a" }}>✓ Auto Approved ({autoApproved.length})</h2>
          {autoApproved.map(s => <SlipCard key={s.thread_id} slip={s} />)}
        </div>

        <div style={styles.column}>
          <h2 style={{ color: "#d97706" }}>⚠ Needs Review ({needsReview.length})</h2>
          {needsReview.map(s => (
            <SlipCard
              key={s.thread_id}
              slip={s}
              onApprove={handleApprove}
              onReject={handleReject}
            />
          ))}
        </div>

        <div style={styles.column}>
          <h2 style={{ color: "#dc2626" }}>✗ Rejected ({rejected.length})</h2>
          {rejected.map(s => <SlipCard key={s.thread_id} slip={s} />)}
        </div>
      </div>
    </div>
  )
}

const styles = {
  page: { fontFamily: "sans-serif", padding: "24px", background: "#f8fafc", minHeight: "100vh" },
  header: { display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "32px" },
  title: { fontSize: "24px", fontWeight: "700", color: "#1e293b" },
  pollBtn: { background: "#2563eb", color: "white", border: "none", padding: "10px 24px", borderRadius: "8px", cursor: "pointer", fontSize: "15px" },
  columns: { display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "24px" },
  column: { background: "white", borderRadius: "12px", padding: "20px", boxShadow: "0 1px 3px rgba(0,0,0,0.1)" },
  card: { border: "1px solid #e2e8f0", borderRadius: "8px", padding: "16px", marginBottom: "12px" },
  cardHeader: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" },
  filename: { fontWeight: "600", fontSize: "14px", color: "#1e293b" },
  badge: { color: "white", fontSize: "11px", padding: "2px 8px", borderRadius: "999px" },
  cardBody: { fontSize: "13px", color: "#475569", lineHeight: "1.8" },
  cardActions: { display: "flex", gap: "8px", marginTop: "12px" },
  approveBtn: { background: "#16a34a", color: "white", border: "none", padding: "6px 16px", borderRadius: "6px", cursor: "pointer" },
  rejectBtn: { background: "#dc2626", color: "white", border: "none", padding: "6px 16px", borderRadius: "6px", cursor: "pointer" },
  label: { fontSize: "12px", fontWeight: "600", color: "#475569", display: "block", marginBottom: "4px" },
  select: { width: "100%", padding: "6px 8px", borderRadius: "6px", border: "1px solid #e2e8f0", fontSize: "13px" },
  input: { width: "100%", padding: "6px 8px", borderRadius: "6px", border: "1px solid #e2e8f0", fontSize: "13px", boxSizing: "border-box" },
}
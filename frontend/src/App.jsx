import { useState, useEffect } from 'react'
import IndexForm from './components/IndexForm'
import QueryForm from './components/QueryForm'
import Result from './components/Result'

const API_BASE = 'http://localhost:8000'

export default function App() {
  const [repoUrl, setRepoUrl] = useState('')
  const [indexing, setIndexing] = useState(false)
  const [indexInfo, setIndexInfo] = useState(null)
  const [question, setQuestion] = useState('')
  const [querying, setQuerying] = useState(false)
  const [results, setResults] = useState([])
  const [error, setError] = useState('')

  async function handleIndex(e) {
    e.preventDefault()
    if (!repoUrl.trim()) return
    setIndexing(true)
    setError('')
    setIndexInfo(null)

    try {
      const res = await fetch(`${API_BASE}/index`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: repoUrl.trim() }),
      })

      const d = await res.json()
      if (!res.ok) { setError(d.detail || 'Indexing failed.'); return }
      setIndexInfo(d)
      setResults([])

    } catch {
      setError('Could not reach the API.')

    } finally {
      setIndexing(false)

    }
  }

  async function handleQuery(e) {
    e.preventDefault()
    if (!question.trim() || !indexInfo) return
    setQuerying(true)
    setError('')

    try {
      const res = await fetch(`${API_BASE}/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: question.trim(), top_k: 6 }),
      })

      const d = await res.json()
      if (!res.ok) { setError(d.detail || 'Query failed.'); return }
      setResults(prev => [d, ...prev])
      setQuestion('')

    } catch {
      setError('Could not reach the API.')

    } finally {
      setQuerying(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col max-w-3xl mx-auto px-4 py-8 gap-8">

      <div className="flex items-center justify-between">
        <h1 className="text-neutral-100 font-mono text-sm font-medium">REPO RAG</h1>
      </div>

      <IndexForm
        repoUrl={repoUrl}
        setRepoUrl={setRepoUrl}
        onSubmit={handleIndex}
        indexing={indexing}
        indexInfo={indexInfo}
      />

      <QueryForm
        question={question}
        setQuestion={setQuestion}
        onSubmit={handleQuery}
        querying={querying}
        disabled={!indexInfo}
      />

      {error && <p className="text-xs text-red-500 font-mono">{error}</p>}

      <section className="flex flex-col gap-8">
        {results.map((r, i) => (
          <Result key={i} data={r} />
        ))}
      </section>

    </div>
  )
}

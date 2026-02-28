export default function QueryForm({ question, setQuestion, topK, setTopK, onSubmit, querying, disabled }) {
  return (
    <form onSubmit={onSubmit} className="flex gap-2 items-center">
      <span className="text-sm font-mono"> Chunks: </span>
      <input
        type="number"
        value={topK}
        onChange={e => setTopK(Number(e.target.value))}
        min={1}
        max={20}
        disabled={disabled || querying}
        className="w-16 bg-neutral-900 border border-neutral-800 rounded px-3 py-2 text-sm text-neutral-200 focus:outline-none focus:border-neutral-600 disabled:opacity-40"
      />
      <span className="text-sm font-mono"> Query: </span>
      <input
        type="text"
        value={question}
        onChange={e => setQuestion(e.target.value)}
        placeholder={disabled ? 'Index a repo first' : 'Ask anything about the codebase...'}
        disabled={disabled || querying}
        className="flex-1 bg-neutral-900 border border-neutral-800 rounded px-3 py-2 text-sm text-neutral-200 placeholder-neutral-600 focus:outline-none focus:border-neutral-600 disabled:opacity-40"
      />
      <button
        type="submit"
        disabled={disabled || querying || !question.trim()}
        className="px-4 py-2 bg-neutral-800 text-neutral-200 text-sm rounded hover:bg-neutral-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
      >
        {querying ? '...' : 'Ask'}
      </button>
    </form>
  )
}

import Chunk from './Chunk'

function renderAnswer(text) {
  // Render backtick-wrapped words as inline code
  const parts = text.split(/(`[^`]+`)/)
  return parts.map((part, i) => {
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code key={i} className="font-mono text-neutral-300 bg-neutral-800 px-1 py-0.5 rounded text-xs">
          {part.slice(1, -1)}
        </code>
      )
    }
    return <span key={i}>{part}</span>
  })
}

export default function Result({ data }) {
  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm text-neutral-400 font-mono">&gt; {data.question}</p>

      <p className="text-sm text-neutral-200 leading-relaxed whitespace-pre-wrap">
        {renderAnswer(data.answer)}
      </p>

      <p className="text-xs text-neutral-600">sources ({data.num_chunks_retrieved})</p>

      <div className="flex flex-col gap-2">
        {data.retrieved_chunks.map((chunk, i) => (
          <Chunk key={i} chunk={chunk} />
        ))}
      </div>
    </div>
  )
}

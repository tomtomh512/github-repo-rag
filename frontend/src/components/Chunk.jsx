import { useState } from 'react'

export default function Chunk({ chunk }) {
  const [expanded, setExpanded] = useState(false)

  return (
    <div className="border border-neutral-800 rounded p-3 flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-mono text-neutral-500 truncate">{chunk.filepath}</span>
        <div className="flex items-center gap-3 shrink-0">
          {chunk.symbol_name && (
            <span className="text-xs font-mono text-neutral-600">{chunk.symbol_name}()</span>
          )}
          <span className="text-xs font-mono text-neutral-500"> Score: {chunk.similarity_score.toFixed(3)}</span>
        </div>
      </div>

      <pre className={`text-xs text-neutral-500 font-mono overflow-x-auto pb-1 leading-relaxed ${expanded ? '' : 'line-clamp-4'}`}>
        {chunk.content}
      </pre>

      <button
        onClick={() => setExpanded(e => !e)}
        className="text-xs text-neutral-700 hover:text-neutral-500 text-left transition-colors w-fit"
      >
        {expanded ? 'Collapse -' : 'Expand +'}
      </button>
    </div>
  )
}

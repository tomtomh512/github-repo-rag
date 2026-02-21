export default function IndexForm({ repoUrl, setRepoUrl, onSubmit, indexing, indexInfo }) {
  return (
    <section className="flex flex-col gap-3">
      <form onSubmit={onSubmit} className="flex gap-2">
        <input
          type="text"
          value={repoUrl}
          onChange={e => setRepoUrl(e.target.value)}
          placeholder="https://github.com/owner/repo"
          className="flex-1 bg-neutral-900 border border-neutral-800 rounded px-3 py-2 text-sm font-mono text-neutral-200 placeholder-neutral-600 focus:outline-none focus:border-neutral-600"
        />
        <button
          type="submit"
          disabled={indexing || !repoUrl.trim()}
          className="px-4 py-2 bg-neutral-800 text-neutral-200 text-sm rounded hover:bg-neutral-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {indexing ? 'Indexing...' : 'Index'}
        </button>
      </form>

      {indexing && (
        <p className="text-xs text-neutral-500 font-mono">
          Cloning and embedding...
        </p>
      )}

      {indexInfo && (
        <div className="flex flex-wrap gap-4 text-xs font-mono text-neutral-500">
          <span className="text-neutral-400">
            {indexInfo.repo?.replace('https://github.com/', '')}
          </span>
          <span>{indexInfo.num_files} files</span>
          <span>{indexInfo.num_chunks} chunks</span>
        </div>
      )}
    </section>
  )
}

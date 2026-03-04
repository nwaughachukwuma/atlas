<script>
  import { onMount } from 'svelte';
  import { listVideos, search } from '../lib/api.js';

  let videos = [];
  let loading = true;
  let error = null;
  let searchQuery = '';
  let searchResults = null;
  let searching = false;

  onMount(async () => {
    try {
      const data = await listVideos();
      videos = data.videos ?? [];
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  });

  async function doSearch() {
    if (!searchQuery.trim()) { searchResults = null; return; }
    searching = true;
    try {
      const data = await search(searchQuery.trim(), null, 20);
      searchResults = data.results ?? [];
    } catch (e) {
      error = e.message;
    } finally {
      searching = false;
    }
  }

  function clearSearch() {
    searchQuery = '';
    searchResults = null;
  }

  function formatDate(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleString();
  }
</script>

<div class="page">
  <h2>🎬 Indexed Videos</h2>
  <p class="desc">All videos currently in your local vector store. Click any video to explore or chat with it.</p>

  <div class="search-bar">
    <input
      type="search"
      bind:value={searchQuery}
      placeholder="Search across all videos…"
      on:keydown={(e) => e.key === 'Enter' && doSearch()}
    />
    <button class="btn-primary" on:click={doSearch} disabled={searching || !searchQuery.trim()}>
      {#if searching}<span class="spinner"></span>{:else}Search{/if}
    </button>
    {#if searchResults !== null}
      <button class="btn-secondary" on:click={clearSearch}>Clear</button>
    {/if}
  </div>

  {#if error}<div class="error-box">{error}</div>{/if}

  {#if searchResults !== null}
    <section>
      <h3>Search results <span class="muted">({searchResults.length})</span></h3>
      {#if searchResults.length === 0}
        <p class="muted">No results found.</p>
      {:else}
        {#each searchResults as r}
          <div class="card result-card">
            <div class="result-header">
              <a href={`#/videos/${r.video_id}`} class="vid-link">{r.video_id}</a>
              <span class="score">score: {r.score?.toFixed(3) ?? '—'}</span>
            </div>
            {#if r.description}<p class="excerpt">{r.description}</p>{/if}
            {#if r.transcript}<p class="excerpt muted">{r.transcript}</p>{/if}
          </div>
        {/each}
      {/if}
    </section>
  {:else}
    {#if loading}
      <p><span class="spinner"></span> Loading videos…</p>
    {:else if videos.length === 0}
      <div class="empty card">
        <p>No videos indexed yet.</p>
        <a href="#/index" class="btn-primary">Index your first video →</a>
      </div>
    {:else}
      <div class="grid">
        {#each videos as v}
          <a href={`#/videos/${v.video_id}`} class="video-card card">
            <div class="vid-icon">🎬</div>
            <div class="vid-meta">
              <span class="vid-id" title={v.video_id}>{v.video_id}</span>
              {#if v.indexed_at}<span class="muted">{formatDate(v.indexed_at)}</span>{/if}
              {#if v.chunk_count !== undefined}<span class="tag">{v.chunk_count} chunks</span>{/if}
            </div>
          </a>
        {/each}
      </div>
    {/if}
  {/if}
</div>

<style>
  .page { padding: 2rem; max-width: 900px; }
  .desc { color: var(--text-muted); margin-bottom: 1.25rem; }
  .muted { color: var(--text-muted); font-size: 0.85rem; }
  .search-bar { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }
  .search-bar input { flex: 1; }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 1rem;
  }
  .video-card {
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
    color: var(--text);
    transition: border-color 0.15s;
  }
  .video-card:hover { border-color: var(--primary); }
  .vid-icon { font-size: 1.8rem; }
  .vid-meta { display: flex; flex-direction: column; gap: 0.25rem; min-width: 0; }
  .vid-id {
    font-size: 0.8rem;
    font-family: monospace;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 150px;
  }
  .empty { text-align: center; padding: 2.5rem; }
  .result-card { margin-bottom: 0.75rem; }
  .result-header { display: flex; justify-content: space-between; margin-bottom: 0.4rem; }
  .vid-link { font-family: monospace; font-size: 0.85rem; color: var(--primary); }
  .score { font-size: 0.78rem; color: var(--text-muted); }
  .excerpt { font-size: 0.85rem; color: var(--text-muted); margin: 0.25rem 0 0; }
  h3 { margin-bottom: 0.75rem; }
</style>

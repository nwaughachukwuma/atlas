<script>
  import { onMount, onDestroy } from 'svelte';
  import { getVideo, search, queueStatus } from '../lib/api.js';
  import ChatPanel from '../components/ChatPanel.svelte';

  export let params = {};
  const videoId = params.id;

  let videoData = null;
  let loading = true;
  let error = null;
  let chatOpen = false;
  let searchQuery = '';
  let searchResults = null;
  let searching = false;
  let pollInterval = null;
  let taskStatus = null;

  async function loadVideo() {
    try {
      const data = await getVideo(videoId);
      videoData = data.data ?? data;
      loading = false;
    } catch (e) {
      if (e.message.includes('404') || e.message.includes('No data')) {
        // may still be indexing via queue — poll queue
        loading = false;
        taskStatus = 'pending';
      } else {
        error = e.message;
        loading = false;
      }
    }
  }

  async function doSearch() {
    if (!searchQuery.trim()) { searchResults = null; return; }
    searching = true;
    try {
      const data = await search(searchQuery.trim(), videoId, 20);
      searchResults = data.results ?? [];
    } catch (e) {
      error = e.message;
    } finally {
      searching = false;
    }
  }

  function clearSearch() { searchQuery = ''; searchResults = null; }

  onMount(async () => {
    await loadVideo();
    if (!videoData) {
      // Poll until video is available (queued indexing)
      pollInterval = setInterval(async () => {
        await loadVideo();
        if (videoData) clearInterval(pollInterval);
      }, 4000);
    }
  });

  onDestroy(() => { if (pollInterval) clearInterval(pollInterval); });

  function formatDate(iso) {
    if (!iso) return '—';
    return new Date(iso).toLocaleString();
  }
</script>

<div class="page">
  <div class="breadcrumb">
    <a href="#/videos">← All Videos</a>
  </div>
  <h2>🎬 Video Detail</h2>
  <code class="vid-id">{videoId}</code>

  {#if loading}
    <div class="loading-state card">
      <span class="spinner"></span>
      <p>Loading video data…</p>
    </div>
  {:else if error}
    <div class="error-box">{error}</div>
  {:else if !videoData}
    <div class="pending-state card">
      <span class="spinner"></span>
      <p>Video is still being indexed… Checking every 4 seconds.</p>
      <p class="muted">This page will update automatically when ready.</p>
    </div>
  {:else}
    <div class="search-bar">
      <input
        type="search"
        bind:value={searchQuery}
        placeholder="Search within this video…"
        on:keydown={(e) => e.key === 'Enter' && doSearch()}
      />
      <button class="btn-primary" on:click={doSearch} disabled={searching || !searchQuery.trim()}>
        {#if searching}<span class="spinner"></span>{:else}Search{/if}
      </button>
      {#if searchResults !== null}
        <button class="btn-secondary" on:click={clearSearch}>Clear</button>
      {/if}
    </div>

    {#if searchResults !== null}
      <section class="card">
        <h3>Search results <span class="muted">({searchResults.length})</span></h3>
        {#if searchResults.length === 0}
          <p class="muted">No results.</p>
        {:else}
          {#each searchResults as r}
            <div class="result-item">
              <span class="score">score: {r.score?.toFixed(3) ?? '—'}</span>
              {#if r.description}<p class="desc-text">{r.description}</p>{/if}
              {#if r.transcript}<p class="muted">{r.transcript}</p>{/if}
            </div>
          {/each}
        {/if}
      </section>
    {:else}
      <div class="meta-card card">
        <h3>Video Info</h3>
        <div class="meta-grid">
          {#each Object.entries(videoData) as [k, v]}
            {#if typeof v !== 'object' || v === null}
              <div class="meta-row">
                <span class="key">{k}</span>
                <span class="val">{v ?? '—'}</span>
              </div>
            {/if}
          {/each}
        </div>
        {#if videoData.chunks}
          <h4 style="margin-top:1rem">Segments ({videoData.chunks.length})</h4>
          {#each videoData.chunks as chunk, i}
            <details>
              <summary>Segment {i + 1}</summary>
              <pre>{JSON.stringify(chunk, null, 2)}</pre>
            </details>
          {/each}
        {/if}
      </div>
    {/if}

    <button class="btn-primary chat-btn" on:click={() => (chatOpen = true)}>
      💬 Chat with this video
    </button>
  {/if}
</div>

{#if chatOpen}
  <ChatPanel {videoId} on:close={() => (chatOpen = false)} />
{/if}

<style>
  .page { padding: 2rem; max-width: 860px; }
  .breadcrumb { margin-bottom: 1rem; font-size: 0.85rem; }
  .vid-id { display: block; font-size: 0.8rem; background: var(--bg3); padding: 0.25em 0.5em; border-radius: 4px; margin: 0.25rem 0 1.25rem; width: fit-content; }
  .muted { color: var(--text-muted); font-size: 0.85rem; }
  .loading-state, .pending-state { text-align: center; padding: 2rem; }
  .loading-state p, .pending-state p { margin: 0.5rem 0; }
  .search-bar { display: flex; gap: 0.5rem; margin-bottom: 1.25rem; }
  .search-bar input { flex: 1; }
  .meta-card h3 { margin-bottom: 0.75rem; }
  .meta-grid { display: flex; flex-direction: column; gap: 0.4rem; }
  .meta-row { display: flex; gap: 1rem; font-size: 0.88rem; }
  .key { color: var(--text-muted); min-width: 130px; }
  .val { color: var(--text); }
  details { border: 1px solid var(--border); border-radius: var(--radius); margin-bottom: 0.4rem; padding: 0.4rem; }
  summary { cursor: pointer; font-size: 0.85rem; color: var(--text-muted); }
  summary:hover { color: var(--primary); }
  .result-item { border-bottom: 1px solid var(--border); padding: 0.75rem 0; }
  .result-item:last-child { border: none; }
  .score { font-size: 0.75rem; color: var(--text-muted); }
  .desc-text { font-size: 0.88rem; margin: 0.25rem 0 0; }
  h3 { margin-bottom: 0.75rem; }
  .chat-btn { margin-top: 1.5rem; font-size: 1rem; padding: 0.6em 1.6em; }
</style>

<script>
  import VideoUpload from '../components/VideoUpload.svelte';
  import { extract } from '../lib/api.js';

  let file = null;
  let chunk_duration = '15s';
  let overlap = '1s';
  let format = 'json';
  let include_summary = true;
  let benchmark = false;
  let no_queue = true;
  let loading = false;
  let result = null;
  let error = null;
  let taskInfo = null;

  async function submit() {
    if (!file) return;
    loading = true; result = null; error = null; taskInfo = null;
    try {
      const data = await extract(file, {
        chunk_duration, overlap, format,
        include_summary, benchmark, no_queue, no_streaming: true,
      });
      if (data.ok === false) { error = data.error || 'Unknown error'; }
      else if (data.task_id || (typeof data === 'object' && 'id' in data && !('chunks' in data))) {
        taskInfo = data;
      } else {
        result = data;
      }
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }
</script>

<div class="page">
  <h2>🔬 Extract Video Insights</h2>
  <p class="desc">Derive rich multimodal understanding — scene descriptions, visual context, and summaries.</p>

  <div class="card">
    <VideoUpload bind:file on:change={() => { result = null; error = null; }} />
  </div>

  <div class="card options">
    <h3>Options</h3>
    <div class="row">
      <div class="form-group">
        <label for="cd">Chunk duration</label>
        <input id="cd" type="text" bind:value={chunk_duration} style="width:90px" />
      </div>
      <div class="form-group">
        <label for="ov">Overlap</label>
        <input id="ov" type="text" bind:value={overlap} style="width:90px" />
      </div>
      <div class="form-group">
        <label for="fmt">Format</label>
        <select id="fmt" bind:value={format}>
          <option value="json">JSON</option>
          <option value="text">Text</option>
        </select>
      </div>
    </div>
    <div class="toggles">
      <label class="toggle">
        <input type="checkbox" bind:checked={include_summary} />
        <span>Include summary</span>
      </label>
      <label class="toggle">
        <input type="checkbox" bind:checked={benchmark} />
        <span>Benchmark timing</span>
      </label>
      <label class="toggle">
        <input type="checkbox" bind:checked={no_queue} />
        <span>Run immediately (no queue)</span>
      </label>
    </div>
  </div>

  <button class="btn-primary submit" on:click={submit} disabled={!file || loading}>
    {#if loading}<span class="spinner"></span> Extracting…{:else}Extract Insights{/if}
  </button>

  {#if error}<div class="error-box">{error}</div>{/if}

  {#if taskInfo}
    <div class="success-box">
      ✅ Task queued! <strong>Task ID:</strong> {taskInfo.task_id ?? taskInfo.id ?? JSON.stringify(taskInfo)}
      <br/><a href="#/queue">View Queue →</a>
    </div>
  {/if}

  {#if result}
    <div class="result card">
      <h3>Extracted Insights</h3>
      {#if result.chunks}
        <p class="muted">{result.chunks.length} segments extracted</p>
        {#each result.chunks as chunk, i}
          <details>
            <summary>Segment {i + 1} — {chunk.start_time ?? ''}s – {chunk.end_time ?? ''}s</summary>
            <pre>{JSON.stringify(chunk, null, 2)}</pre>
          </details>
        {/each}
        {#if result.summary}
          <div class="summary">
            <h4>Summary</h4>
            <p>{result.summary}</p>
          </div>
        {/if}
      {:else}
        <pre>{JSON.stringify(result, null, 2)}</pre>
      {/if}
    </div>
  {/if}
</div>

<style>
  .page { padding: 2rem; max-width: 760px; }
  .desc { color: var(--text-muted); margin-bottom: 1.25rem; }
  .muted { color: var(--text-muted); font-size: 0.85rem; }
  .options h3 { margin-bottom: 0.75rem; }
  .toggles { display: flex; flex-direction: column; gap: 0.5rem; margin-top: 0.75rem; }
  .toggle { display: flex; align-items: center; gap: 0.5rem; cursor: pointer; font-size: 0.88rem; }
  .toggle input { accent-color: var(--primary); }
  .card { margin-bottom: 1rem; }
  .submit { margin-bottom: 0.75rem; font-size: 1rem; padding: 0.6em 1.6em; }
  details { border: 1px solid var(--border); border-radius: var(--radius); margin-bottom: 0.5rem; padding: 0.5rem; }
  summary { cursor: pointer; font-size: 0.88rem; color: var(--text-muted); }
  summary:hover { color: var(--primary); }
  .summary { margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border); }
  .summary h4 { margin-bottom: 0.4rem; }
  select { width: 100px; }
</style>

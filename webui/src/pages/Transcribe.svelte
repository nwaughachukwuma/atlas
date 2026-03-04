<script>
  import VideoUpload from '../components/VideoUpload.svelte';
  import { transcribe } from '../lib/api.js';

  let file = null;
  let format = 'text';
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
      const data = await transcribe(file, { format, benchmark, no_queue, no_streaming: true });
      if (data.ok === false) { error = data.error || 'Unknown error'; }
      else if (data.task_id) { taskInfo = data; }
      else { result = data; }
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }
</script>

<div class="page">
  <h2>🎙️ Transcribe Video</h2>
  <p class="desc">Convert your video's audio to text. Supports plain text, WebVTT, and SRT formats.</p>

  <div class="card">
    <VideoUpload bind:file on:change={() => { result = null; error = null; }} />
  </div>

  <div class="card options">
    <h3>Options</h3>
    <div class="row">
      <div class="form-group">
        <label for="fmt">Output format</label>
        <select id="fmt" bind:value={format}>
          <option value="text">Plain text</option>
          <option value="vtt">WebVTT</option>
          <option value="srt">SRT</option>
        </select>
      </div>
    </div>
    <div class="toggles">
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
    {#if loading}<span class="spinner"></span> Transcribing…{:else}Transcribe{/if}
  </button>

  {#if error}
    <div class="error-box">{error}</div>
  {/if}

  {#if taskInfo}
    <div class="success-box">
      ✅ Task queued! <strong>Task ID:</strong> {taskInfo.task_id ?? taskInfo.id ?? JSON.stringify(taskInfo)}
      <br/><a href="#/queue">View Queue →</a>
    </div>
  {/if}

  {#if result}
    <div class="result card">
      <h3>Transcript <span class="tag">{format}</span></h3>
      {#if result.transcript}
        <pre>{result.transcript}</pre>
      {:else}
        <pre>{JSON.stringify(result, null, 2)}</pre>
      {/if}
    </div>
  {/if}
</div>

<style>
  .page { padding: 2rem; max-width: 760px; }
  .desc { color: var(--text-muted); margin-bottom: 1.25rem; }
  .options h3 { margin-bottom: 0.75rem; }
  .toggles { display: flex; flex-direction: column; gap: 0.5rem; margin-top: 0.75rem; }
  .toggle { display: flex; align-items: center; gap: 0.5rem; cursor: pointer; font-size: 0.88rem; }
  .toggle input { accent-color: var(--primary); }
  .card { margin-bottom: 1rem; }
  .submit { margin-bottom: 0.75rem; font-size: 1rem; padding: 0.6em 1.6em; }
  .result h3 { margin-bottom: 0.75rem; }
  select { width: 160px; }
</style>

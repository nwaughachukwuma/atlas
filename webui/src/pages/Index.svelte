<script>
  import { DatabaseIcon, CircleCheckIcon } from "lucide-svelte";
  import VideoUpload from "../components/VideoUpload.svelte";
  import { indexVideo } from "../lib/api.js";

  let file = null;
  let chunk_duration = "15s";
  let overlap = "1s";
  let include_summary = true;
  let benchmark = false;
  let no_queue = true;
  let loading = false;
  let result = null;
  let error = null;
  let taskInfo = null;

  async function submit() {
    if (!file) return;
    loading = true;
    result = null;
    error = null;
    taskInfo = null;
    try {
      const data = await indexVideo(file, {
        chunk_duration,
        overlap,
        include_summary,
        benchmark,
        no_queue,
        no_streaming: true,
      });
      if (data.ok === false) {
        error = data.error || "Unknown error";
      } else if (data.task_id) {
        taskInfo = data;
      } else if (data.video_id) {
        result = data;
      } else if ("id" in data && !("video_id" in data)) {
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
  <h2>
    <DatabaseIcon
      size={20}
      strokeWidth={2}
      style="display:inline;vertical-align:middle;"
    /> Index Video
  </h2>
  <p class="desc">
    Index your video for semantic search and conversational chat. Chunks are
    stored locally in a vector store for instant retrieval.
  </p>

  <div class="card">
    <VideoUpload
      bind:file
      on:change={() => {
        result = null;
        error = null;
      }}
    />
  </div>

  <div class="card options">
    <h3>Options</h3>
    <div class="row">
      <div class="form-group">
        <label for="cd">Chunk duration</label>
        <input
          id="cd"
          type="text"
          bind:value={chunk_duration}
          style="width:90px"
        />
      </div>
      <div class="form-group">
        <label for="ov">Overlap</label>
        <input id="ov" type="text" bind:value={overlap} style="width:90px" />
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

  <button
    class="btn-primary submit"
    on:click={submit}
    disabled={!file || loading}
  >
    {#if loading}<span class="spinner"></span> Indexing…{:else}Index Video{/if}
  </button>

  {#if error}<div class="error-box">{error}</div>{/if}

  {#if taskInfo}
    <div class="success-box">
      <CircleCheckIcon
        size={16}
        strokeWidth={2}
        style="display:inline;vertical-align:middle;"
      /> Task queued! <strong>Task ID:</strong>
      {taskInfo.task_id ?? taskInfo.id ?? JSON.stringify(taskInfo)}
      <br /><a href="#/queue">View Queue →</a>
    </div>
  {/if}

  {#if result}
    <div class="result card">
      <h3>
        <CircleCheckIcon
          size={18}
          strokeWidth={2}
          style="display:inline;vertical-align:middle;"
        /> Indexed Successfully
      </h3>
      <p><strong>Video ID:</strong> <code>{result.video_id}</code></p>
      <p><strong>Indexed chunks:</strong> {result.indexed_count}</p>
      <a
        href={`#/videos/${result.video_id}`}
        class="btn-primary"
        style="display:inline-block;margin-top:0.5rem"
      >
        View Video →
      </a>
      {#if result.result}
        <details style="margin-top:1rem">
          <summary>Full result JSON</summary>
          <pre>{JSON.stringify(result.result, null, 2)}</pre>
        </details>
      {/if}
    </div>
  {/if}
</div>

<style>
  .page {
    padding: 2rem;
    max-width: 760px;
  }
  .desc {
    color: var(--text-muted);
    margin-bottom: 1.25rem;
  }
  .options h3 {
    margin-bottom: 0.75rem;
  }
  .toggles {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    margin-top: 0.75rem;
  }
  .toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    font-size: 0.88rem;
  }
  .toggle input {
    accent-color: var(--primary);
  }
  .card {
    margin-bottom: 1rem;
  }
  .submit {
    margin-bottom: 0.75rem;
    font-size: 1rem;
    padding: 0.6em 1.6em;
  }
  code {
    background: var(--bg3);
    padding: 0.15em 0.4em;
    border-radius: 4px;
    font-size: 0.85em;
  }
  details {
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.5rem;
  }
  summary {
    cursor: pointer;
    font-size: 0.88rem;
    color: var(--text-muted);
  }
</style>

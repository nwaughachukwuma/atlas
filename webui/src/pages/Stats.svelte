<script>
  import { ChartBarIcon, CircleCheckIcon, CircleXIcon } from "lucide-svelte";
  import { onMount } from "svelte";
  import { stats, health } from "../lib/api.js";

  let data = null;
  let healthData = null;
  let loading = true;
  let error = null;

  onMount(async () => {
    try {
      [data, healthData] = await Promise.all([stats(), health()]);
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  });

  function fmt(val) {
    if (val === null || val === undefined) return "—";
    if (typeof val === "object") return JSON.stringify(val, null, 2);
    return String(val);
  }
</script>

<div class="page">
  <h2>
    <ChartBarIcon
      size={20}
      strokeWidth={2}
      style="display:inline;vertical-align:middle;"
    /> System Stats
  </h2>
  <p class="desc">
    Overview of the vector store, task queue, and system health.
  </p>

  {#if loading}
    <p><span class="spinner"></span> Loading…</p>
  {:else if error}
    <div class="error-box">{error}</div>
  {:else}
    <div class="grid">
      <div class="card stat-card">
        <h3>Health</h3>
        <div class:healthy={healthData?.status === "ok"} class="health-badge">
          {#if healthData?.status === "ok"}
            <CircleCheckIcon
              size={16}
              strokeWidth={2}
              style="display:inline;vertical-align:middle;"
            /> Online
          {:else}
            <CircleXIcon
              size={16}
              strokeWidth={2}
              style="display:inline;vertical-align:middle;"
            /> Offline
          {/if}
        </div>
      </div>

      <div class="card stat-card">
        <h3>Videos Indexed</h3>
        <span class="big-num">{data?.videos_indexed ?? "—"}</span>
      </div>
    </div>

    <div class="card details">
      <h3>Storage Paths</h3>
      <div class="meta-grid">
        <div class="meta-row">
          <span class="key">Video index</span>
          <code>{data?.video_col_path ?? "—"}</code>
        </div>
        <div class="meta-row">
          <span class="key">Chat store</span>
          <code>{data?.chat_col_path ?? "—"}</code>
        </div>
      </div>
    </div>

    <div class="card details">
      <h3>Index Stats</h3>
      {#if data?.video_index_stats}
        <pre>{data.video_index_stats}</pre>
      {:else}
        <p class="muted">No stats available.</p>
      {/if}
    </div>

    <div class="card details">
      <h3>Chat Stats</h3>
      {#if data?.chat_index_stats}
        <pre>{data.chat_index_stats}</pre>
      {:else}
        <p class="muted">No stats available.</p>
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
    margin-bottom: 1.5rem;
  }
  .muted {
    color: var(--text-muted);
    font-size: 0.85rem;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
  }
  .stat-card h3 {
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .big-num {
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--primary);
  }
  .health-badge {
    font-size: 1.1rem;
    font-weight: 600;
  }
  .healthy {
    color: var(--success);
  }
  .details {
    margin-bottom: 1rem;
  }
  .details h3 {
    margin-bottom: 0.75rem;
  }
  .meta-grid {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .meta-row {
    display: flex;
    gap: 1rem;
    font-size: 0.88rem;
    align-items: flex-start;
  }
  .key {
    color: var(--text-muted);
    min-width: 120px;
  }
  code {
    font-size: 0.8rem;
    background: var(--bg3);
    padding: 0.15em 0.4em;
    border-radius: 4px;
    word-break: break-all;
  }
</style>

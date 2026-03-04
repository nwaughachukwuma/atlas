<script>
  import { ClipboardListIcon } from "lucide-svelte";
  import { onMount, onDestroy } from "svelte";
  import { queueList, queueStatus } from "../lib/api.js";

  export let params = {};
  const taskId = params.id ?? null;

  let tasks = [];
  let task = null;
  let loading = true;
  let error = null;
  let statusFilter = null;
  let pollInterval = null;

  const statusOptions = [
    null,
    "pending",
    "running",
    "completed",
    "failed",
    "timeout",
  ];

  async function load() {
    try {
      if (taskId) {
        task = await queueStatus(taskId);
      } else {
        const data = await queueList(statusFilter);
        tasks = data.tasks ?? [];
      }
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  onMount(async () => {
    await load();
    // Auto-refresh when there are active tasks
    pollInterval = setInterval(async () => {
      const hasActive =
        tasks.some((t) => t.status === "pending" || t.status === "running") ||
        (task && (task.status === "pending" || task.status === "running"));
      if (hasActive) await load();
    }, 5000);
  });

  onDestroy(() => {
    if (pollInterval) clearInterval(pollInterval);
  });

  function badgeClass(status) {
    return `badge badge-${status ?? "pending"}`;
  }

  function formatDate(iso) {
    if (!iso) return "—";
    return new Date(iso).toLocaleString();
  }
</script>

<div class="page">
  {#if taskId}
    <!-- Single task view -->
    <div class="breadcrumb"><a href="#/queue">← All Tasks</a></div>
    <h2>
      <ClipboardListIcon
        size={20}
        strokeWidth={2}
        style="display:inline;vertical-align:middle;"
      /> Task Detail
    </h2>
    {#if loading}
      <p><span class="spinner"></span> Loading…</p>
    {:else if error}
      <div class="error-box">{error}</div>
    {:else if task}
      <div class="card task-detail">
        <div class="task-header">
          <span class:active={task.status === "running"} class="status-dot"
          ></span>
          <code>{task.id}</code>
          <span class={badgeClass(task.status)}>{task.status}</span>
        </div>
        <div class="meta-grid">
          <div class="meta-row">
            <span class="key">Command</span><span class="val"
              >{task.command}</span
            >
          </div>
          <div class="meta-row">
            <span class="key">Label</span><span class="val">{task.label}</span>
          </div>
          <div class="meta-row">
            <span class="key">Created</span><span class="val"
              >{formatDate(task.created_at)}</span
            >
          </div>
          <div class="meta-row">
            <span class="key">Started</span><span class="val"
              >{formatDate(task.started_at)}</span
            >
          </div>
          <div class="meta-row">
            <span class="key">Finished</span><span class="val"
              >{formatDate(task.finished_at)}</span
            >
          </div>
          {#if task.duration}<div class="meta-row">
              <span class="key">Duration</span><span class="val"
                >{task.duration}</span
              >
            </div>{/if}
        </div>
        {#if task.error}
          <div class="error-box" style="margin-top:1rem">{task.error}</div>
        {/if}
        {#if task.output_path}
          <div class="success-box" style="margin-top:1rem">
            Output: <code>{task.output_path}</code>
          </div>
        {/if}
        {#if task.status === "pending" || task.status === "running"}
          <p class="muted" style="margin-top:1rem">
            <span class="spinner"></span> Refreshing every 5s…
          </p>
        {/if}
      </div>
    {/if}
  {:else}
    <!-- Task list view -->
    <h2 class="flex items-center gap-1.5">
      <ClipboardListIcon
        size={20}
        strokeWidth={2}
        style="display:inline;vertical-align:middle;"
      /> Task Queue
    </h2>
    <p class="desc">Monitor and inspect background tasks.</p>

    <div class="filters">
      {#each statusOptions as s}
        <button
          class={statusFilter === s ? "btn-primary" : "btn-secondary"}
          on:click={() => {
            statusFilter = s;
            load();
          }}
        >
          {s ?? "All"}
        </button>
      {/each}
      <button class="btn-secondary" on:click={load} title="Refresh"
        >↻ Refresh</button
      >
    </div>

    {#if loading}
      <p><span class="spinner"></span> Loading…</p>
    {:else if error}
      <div class="error-box">{error}</div>
    {:else if tasks.length === 0}
      <div class="empty card"><p>No tasks found.</p></div>
    {:else}
      <div class="task-list">
        {#each tasks as t}
          <a href={`#/queue/${t.id}`} class="task-row card">
            <div class="task-main">
              <span class={badgeClass(t.status)}>{t.status}</span>
              <span class="cmd tag">{t.command}</span>
              <span class="label">{t.label}</span>
            </div>
            <div class="task-sub">
              <code class="tid">{t.id}</code>
              <span class="muted">{formatDate(t.created_at)}</span>
            </div>
          </a>
        {/each}
      </div>
    {/if}
  {/if}
</div>

<style>
  .page {
    padding: 2rem;
    max-width: 860px;
  }
  .breadcrumb {
    margin-bottom: 1rem;
    font-size: 0.85rem;
  }
  .desc {
    color: var(--text-muted);
    margin-bottom: 1.25rem;
  }
  .muted {
    color: var(--text-muted);
    font-size: 0.85rem;
  }
  .filters {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin-bottom: 1.25rem;
  }
  .task-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .task-row {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    color: var(--text);
    transition: border-color 0.15s;
  }
  .task-row:hover {
    border-color: var(--primary);
  }
  .task-main {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .task-sub {
    display: flex;
    gap: 1rem;
    align-items: center;
  }
  .label {
    font-size: 0.88rem;
    flex: 1;
  }
  .cmd {
    font-size: 0.78rem;
  }
  .tid {
    font-size: 0.75rem;
    font-family: monospace;
    color: var(--text-muted);
  }
  .empty {
    text-align: center;
    padding: 2rem;
  }
  .task-detail code {
    font-size: 0.82rem;
  }
  .task-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 1rem;
  }
  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--text-muted);
  }
  .status-dot.active {
    background: var(--info);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
    animation: pulse 1.5s infinite;
  }
  @keyframes pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }
  .meta-grid {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }
  .meta-row {
    display: flex;
    gap: 1rem;
    font-size: 0.88rem;
  }
  .key {
    color: var(--text-muted);
    min-width: 100px;
  }
  .val {
    color: var(--text);
  }
</style>

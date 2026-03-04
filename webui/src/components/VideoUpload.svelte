<script>
  import { FilmIcon, UploadIcon, XIcon } from "lucide-svelte";
  import { createEventDispatcher } from "svelte";
  const dispatch = createEventDispatcher();

  export let accept = "video/*";
  export let file = null;

  let dragging = false;
  let input;

  function handleDrop(e) {
    e.preventDefault();
    dragging = false;
    const f = e.dataTransfer?.files[0];
    if (f) setFile(f);
  }

  function setFile(f) {
    file = f;
    dispatch("change", f);
  }

  function handleInput(e) {
    const f = e.target.files[0];
    if (f) setFile(f);
  }

  function clear() {
    file = null;
    if (input) input.value = "";
    dispatch("change", null);
  }

  function formatSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  }
</script>

<div
  class="dropzone"
  class:dragging
  class:has-file={!!file}
  on:dragover|preventDefault={() => (dragging = true)}
  on:dragleave={() => (dragging = false)}
  on:drop={handleDrop}
  role="region"
  aria-label="Video file upload"
>
  {#if file}
    <div class="file-info">
      <span class="icon"><FilmIcon size={20} strokeWidth={1.5} /></span>
      <div class="meta">
        <span class="name">{file.name}</span>
        <span class="size">{formatSize(file.size)}</span>
      </div>
      <button
        type="button"
        class="btn-remove"
        on:click={clear}
        title="Remove file"><XIcon size={16} strokeWidth={2} /></button
      >
    </div>
  {:else}
    <div class="prompt">
      <span class="icon"><UploadIcon size={28} strokeWidth={1.5} /></span>
      <p>Drag &amp; drop a video file here</p>
      <span class="or">or</span>
      <!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
      <label class="btn-secondary" style="cursor:pointer;">
        Browse files
        <input
          bind:this={input}
          type="file"
          {accept}
          on:change={handleInput}
          hidden
        />
      </label>
    </div>
  {/if}
</div>

<style>
  .dropzone {
    border: 2px dashed var(--border);
    border-radius: var(--radius);
    padding: 2rem;
    text-align: center;
    transition: all 0.15s;
    background: var(--bg3);
    cursor: pointer;
  }
  .dropzone.dragging {
    border-color: var(--primary);
    background: rgba(99, 102, 241, 0.07);
  }
  .dropzone.has-file {
    border-style: solid;
    border-color: var(--success);
    padding: 1rem;
  }
  .prompt .icon {
    color: var(--color-cobalt);
    display: flex;
    justify-content: center;
    margin-bottom: 0.5rem;
  }
  .prompt p {
    color: var(--text-muted);
    margin: 0.25rem 0 0.75rem;
    font-size: 0.9rem;
  }
  .or {
    color: var(--text-muted);
    font-size: 0.8rem;
    display: block;
    margin-bottom: 0.5rem;
  }
  .file-info {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    text-align: left;
  }
  .file-info .icon {
    font-size: 1.5rem;
  }
  .meta {
    flex: 1;
  }
  .name {
    display: block;
    font-size: 0.9rem;
    font-weight: 500;
  }
  .size {
    display: block;
    font-size: 0.78rem;
    color: var(--text-muted);
  }
  .btn-remove {
    background: none;
    border: none;
    color: var(--text-muted);
    font-size: 1rem;
    padding: 0.25rem;
    line-height: 1;
  }
  .btn-remove:hover {
    color: var(--danger);
  }
</style>

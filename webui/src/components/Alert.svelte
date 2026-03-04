<script>
  import {
    CircleAlertIcon,
    CircleCheckIcon,
    InfoIcon,
    XIcon,
  } from "lucide-svelte";

  /** @type {'error' | 'success' | 'info'} */
  export let type = "error";
  export let message = "";
  export let dismissible = false;

  let visible = true;

  $: if (message) visible = true;
</script>

{#if visible && message}
  <div
    class="alert"
    class:alert-error={type === "error"}
    class:alert-success={type === "success"}
    class:alert-info={type === "info"}
    role="alert"
  >
    <div class="alert-icon">
      {#if type === "error"}<CircleAlertIcon size={15} />{/if}
      {#if type === "success"}<CircleCheckIcon size={15} />{/if}
      {#if type === "info"}<InfoIcon size={15} />{/if}
    </div>
    <span class="alert-msg">{message}</span>
    {#if dismissible}
      <button
        class="alert-close"
        on:click={() => (visible = false)}
        aria-label="Dismiss"
      >
        <XIcon size={13} />
      </button>
    {/if}
  </div>
{/if}

<style>
  .alert {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    padding: 0.65rem 0.9rem;
    margin: 0.75rem 0;
    font-size: 0.83rem;
    font-family: var(--font-mono);
    border: 1px solid;
    line-height: 1.4;
  }
  .alert-error {
    background: #18070a;
    border-color: #7f1d1d;
    color: #fca5a5;
  }
  .alert-success {
    background: #011a11;
    border-color: #065f46;
    color: #6ee7b7;
  }
  .alert-info {
    background: #0c1a2e;
    border-color: #1e3a5f;
    color: #93c5fd;
  }
  .alert-icon {
    flex-shrink: 0;
    margin-top: 0.05em;
    display: flex;
  }
  .alert-msg {
    flex: 1;
    word-break: break-word;
  }
  .alert-close {
    flex-shrink: 0;
    background: transparent;
    border: none;
    padding: 0;
    color: inherit;
    opacity: 0.6;
    cursor: pointer;
    display: flex;
    margin-top: 0.1em;
  }
  .alert-close:hover {
    opacity: 1;
  }
</style>

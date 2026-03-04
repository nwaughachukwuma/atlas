<script>
  import { CircleQuestionMarkIcon, XIcon } from "lucide-svelte";

  let open = false;

  const steps = [
    {
      num: "01",
      action: "Upload",
      detail: "Drop or browse a video file — any common format accepted.",
    },
    {
      num: "02",
      action: "Choose",
      detail:
        "Pick an operation: Transcribe, Extract Insights, or Index for chat.",
    },
    {
      num: "03",
      action: "Configure",
      detail: "Set chunk duration, output format, queuing preferences.",
    },
    {
      num: "04",
      action: "Submit",
      detail: "Results stream in immediately, or tasks are queued for later.",
    },
    {
      num: "05",
      action: "Chat",
      detail: "Ask questions in natural language about any indexed video.",
    },
  ];
</script>

<button class="help-btn" on:click={() => (open = true)} title="How it works">
  <CircleQuestionMarkIcon size={18} strokeWidth={1.5} />
  <span>How it works</span>
</button>

{#if open}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div class="backdrop" on:click={() => (open = false)}>
    <div
      class="dialog"
      on:click|stopPropagation
      role="dialog"
      tabindex="0"
      aria-modal="true"
      aria-label="How it works"
    >
      <div class="dialog-header">
        <span class="dialog-title">How it works</span>
        <button
          class="close-btn"
          on:click={() => (open = false)}
          aria-label="Close"
        >
          <XIcon size={16} />
        </button>
      </div>
      <ol class="steps">
        {#each steps as s}
          <li class="step">
            <span class="step-num">{s.num}</span>
            <div class="step-body">
              <strong>{s.action}</strong>
              <span>{s.detail}</span>
            </div>
          </li>
        {/each}
      </ol>
    </div>
  </div>
{/if}

<style>
  /* Trigger button — positioned by parent */
  .help-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: transparent;
    border: 1px solid var(--color-line);
    color: var(--color-text-muted);
    font-family: var(--font-display);
    font-size: 0.8rem;
    font-weight: 600;
    padding: 0.38em 0.75em;
    letter-spacing: 0.01em;
    cursor: pointer;
    transition: all 0.3s linear;
    white-space: nowrap;
  }
  .help-btn:hover {
    border-color: var(--color-cobalt);
    color: var(--color-cobalt);
  }

  /* Backdrop */
  .backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 999;
  }

  /* Dialog */
  .dialog {
    background: var(--color-surface);
    border: 1px solid var(--color-line);
    width: 480px;
    max-width: 92vw;
    max-height: 85vh;
    overflow-y: auto;
  }

  .dialog-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--color-line);
  }

  .dialog-title {
    font-family: var(--font-display);
    font-size: 0.95rem;
    font-weight: 700;
    letter-spacing: -0.01em;
    text-transform: uppercase;
    color: var(--color-text);
  }

  .close-btn {
    background: transparent;
    border: none;
    color: var(--color-text-muted);
    cursor: pointer;
    padding: 0.2em;
    display: flex;
    align-items: center;
  }
  .close-btn:hover {
    color: var(--color-text);
  }

  /* Steps */
  .steps {
    list-style: none;
    margin: 0;
    padding: 0.5rem 0;
  }

  .step {
    display: flex;
    gap: 1rem;
    align-items: flex-start;
    padding: 0.9rem 1.25rem;
    border-bottom: 1px solid var(--color-line);
  }
  .step:last-child {
    border-bottom: none;
  }

  .step-num {
    font-family: var(--font-mono);
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--color-cobalt);
    opacity: 0.7;
    min-width: 2.2rem;
    padding-top: 0.1em;
    letter-spacing: 0.04em;
  }

  .step-body {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }

  .step-body strong {
    font-family: var(--font-display);
    font-size: 0.88rem;
    font-weight: 700;
    color: var(--color-text);
    letter-spacing: -0.005em;
  }

  .step-body span {
    font-size: 0.83rem;
    color: var(--color-text-secondary);
    line-height: 1.4;
  }
</style>

<script>
  import { createEventDispatcher, onDestroy } from 'svelte';
  import { chatStream, listChat } from '../lib/api.js';

  export let videoId;

  const dispatch = createEventDispatcher();

  let messages = [];
  let query = '';
  let streaming = false;
  let ctrl = null;
  let listEl;

  async function loadHistory() {
    try {
      const data = await listChat(videoId);
      messages = (data.messages || []).map((m) => ({
        role: m.role ?? (m.query ? 'user' : 'assistant'),
        text: m.content ?? m.query ?? m.answer ?? JSON.stringify(m),
      }));
    } catch (_) { /* ignore */ }
  }

  loadHistory();

  function scrollBottom() {
    if (listEl) setTimeout(() => { listEl.scrollTop = listEl.scrollHeight; }, 50);
  }

  async function send() {
    const q = query.trim();
    if (!q || streaming) return;
    query = '';
    messages = [...messages, { role: 'user', text: q }];
    messages = [...messages, { role: 'assistant', text: '' }];
    streaming = true;
    scrollBottom();

    ctrl = chatStream(
      videoId, q,
      (chunk) => {
        messages[messages.length - 1].text += chunk;
        messages = messages;
        scrollBottom();
      },
      () => { streaming = false; ctrl = null; },
    );
  }

  function cancel() {
    ctrl?.abort();
    streaming = false;
  }

  onDestroy(() => ctrl?.abort());

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  }
</script>

<div class="panel">
  <div class="panel-header">
    <span>💬 Chat with Video</span>
    <button class="close-btn btn-secondary" on:click={() => dispatch('close')}>✕</button>
  </div>
  <div class="messages" bind:this={listEl}>
    {#if messages.length === 0}
      <p class="empty">Ask a question about this video…</p>
    {/if}
    {#each messages as m}
      <div class="msg" class:user={m.role === 'user'} class:assistant={m.role === 'assistant'}>
        <span class="bubble">{m.text || (streaming && m.role === 'assistant' ? '…' : '')}</span>
      </div>
    {/each}
  </div>
  <div class="input-row">
    <textarea
      bind:value={query}
      on:keydown={handleKey}
      placeholder="Ask something… (Enter to send)"
      rows="2"
      disabled={streaming}
    ></textarea>
    {#if streaming}
      <button class="btn-danger" on:click={cancel}>Stop</button>
    {:else}
      <button class="btn-primary" on:click={send} disabled={!query.trim()}>Send</button>
    {/if}
  </div>
</div>

<style>
  .panel {
    position: fixed;
    bottom: 1.5rem;
    right: 1.5rem;
    width: 380px;
    max-height: 520px;
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 12px;
    box-shadow: var(--shadow);
    display: flex;
    flex-direction: column;
    z-index: 1000;
  }
  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border);
    font-weight: 600;
    font-size: 0.9rem;
  }
  .close-btn { padding: 0.2em 0.6em; }
  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 0.75rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  .empty { color: var(--text-muted); font-size: 0.85rem; text-align: center; margin: auto; }
  .msg { display: flex; }
  .msg.user { justify-content: flex-end; }
  .bubble {
    max-width: 80%;
    padding: 0.5em 0.8em;
    border-radius: 10px;
    font-size: 0.88rem;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .user .bubble { background: var(--primary); color: #fff; }
  .assistant .bubble { background: var(--bg3); color: var(--text); }
  .input-row {
    display: flex;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    border-top: 1px solid var(--border);
  }
  textarea { flex: 1; resize: none; font-size: 0.85rem; }
  button { align-self: flex-end; white-space: nowrap; }
</style>

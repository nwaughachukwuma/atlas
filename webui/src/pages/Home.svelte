<script>
  const features = [
    {
      path: '/transcribe',
      icon: '🎙️',
      title: 'Transcribe',
      desc: 'Convert video audio to text in plain text, VTT, or SRT format.',
    },
    {
      path: '/extract',
      icon: '🔬',
      title: 'Extract Insights',
      desc: 'Derive rich multimodal understanding from your video — scenes, descriptions, and summaries.',
    },
    {
      path: '/index',
      icon: '📦',
      title: 'Index Video',
      desc: 'Index a video for semantic search and chat. Stored locally for instant retrieval.',
    },
    {
      path: '/videos',
      icon: '🎬',
      title: 'Browse Videos',
      desc: 'View all indexed videos, search across them, and chat with any video.',
    },
    {
      path: '/queue',
      icon: '📋',
      title: 'Task Queue',
      desc: 'Monitor and manage background tasks for long-running video operations.',
    },
    {
      path: '/stats',
      icon: '📊',
      title: 'System Stats',
      desc: 'Inspect the vector index, chat store, and overall system health.',
    },
  ];
</script>

<div class="home">
  <header>
    <h1>⚡ Atlas <span class="accent">Video</span></h1>
    <p class="subtitle">
      A multimodal AI engine for video insights — transcription, semantic extraction,
      semantic search, and conversational chat. All running locally.
    </p>
  </header>

  <section class="features">
    {#each features as f}
      <a href={`#${f.path}`} class="feature-card card">
        <span class="feat-icon">{f.icon}</span>
        <h3>{f.title}</h3>
        <p>{f.desc}</p>
        <span class="go-btn">Explore →</span>
      </a>
    {/each}
  </section>

  <section class="how card">
    <h2>How it works</h2>
    <ol>
      <li><strong>Upload</strong> a video file (any common format).</li>
      <li><strong>Choose</strong> an operation: transcribe, extract, or index.</li>
      <li><strong>Configure</strong> options like chunk duration, output format, and queuing.</li>
      <li><strong>Submit</strong> and watch results stream in — or queue for later.</li>
      <li><strong>Chat</strong> with indexed videos to ask questions in natural language.</li>
    </ol>
  </section>
</div>

<style>
  .home { padding: 2rem; max-width: 960px; }
  header { margin-bottom: 2.5rem; }
  h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
  .accent { color: var(--primary); }
  .subtitle { color: var(--text-muted); font-size: 1.05rem; max-width: 580px; }
  .features {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
  }
  .feature-card {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    color: var(--text);
    transition: border-color 0.15s, transform 0.15s;
  }
  .feature-card:hover {
    border-color: var(--primary);
    transform: translateY(-2px);
  }
  .feat-icon { font-size: 1.8rem; }
  .feature-card h3 { margin: 0; font-size: 1rem; }
  .feature-card p { color: var(--text-muted); font-size: 0.85rem; flex: 1; margin: 0; }
  .go-btn { color: var(--primary); font-size: 0.85rem; font-weight: 600; }
  .how { max-width: 560px; }
  .how h2 { margin-bottom: 0.75rem; }
  .how ol { margin: 0; padding-left: 1.4em; color: var(--text-muted); }
  .how li { margin-bottom: 0.4em; font-size: 0.9rem; }
  .how li strong { color: var(--text); }
</style>

<script>
  import {
    MicIcon,
    FlaskConicalIcon,
    DatabaseIcon,
    FilmIcon,
    ClipboardListIcon,
    LayoutDashboardIcon,
    ZapIcon,
  } from "lucide-svelte";

  const features = [
    {
      path: "/transcribe",
      icon: MicIcon,
      title: "Transcribe",
      desc: "Convert video audio to text in plain text, VTT, or SRT format.",
    },
    {
      path: "/extract",
      icon: FlaskConicalIcon,
      title: "Extract Insights",
      desc: "Derive rich multimodal understanding from your video — scenes, descriptions, and summaries.",
    },
    {
      path: "/index",
      icon: DatabaseIcon,
      title: "Index Video",
      desc: "Index a video for semantic search and chat. Stored locally for instant retrieval.",
    },
    {
      path: "/videos",
      icon: FilmIcon,
      title: "Browse Videos",
      desc: "View all indexed videos, search across them, and chat with any video.",
    },
    {
      path: "/queue",
      icon: ClipboardListIcon,
      title: "Task Queue",
      desc: "Monitor and manage background tasks for long-running video operations.",
    },
    {
      path: "/dashboard",
      icon: LayoutDashboardIcon,
      title: "Dashboard",
      desc: "System health, video & chat counts, queue status, and storage overview.",
    },
  ];
</script>

<div class="home">
  <header>
    <h1>
      <ZapIcon
        size={28}
        strokeWidth={2.5}
        style="display:inline;vertical-align:baseline;"
      /> Atlas <span class="accent">Video</span>
    </h1>
    <p class="subtitle">
      Multimodal AI engine for video insights — transcription, semantic
      extraction, semantic search, and conversational chat. All running locally.
    </p>
  </header>

  <section class="features">
    {#each features as f}
      <a href={`#${f.path}`} class="feature-card card">
        <span class="feat-icon"
          ><svelte:component this={f.icon} size={24} strokeWidth={1.5} /></span
        >
        <h3>{f.title}</h3>
        <p>{f.desc}</p>
        <span class="go-btn">Explore →</span>
      </a>
    {/each}
  </section>
</div>

<style>
  .home {
    padding: 2rem;
    max-width: 960px;
  }
  header {
    margin-bottom: 2.5rem;
  }
  h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
  }
  .accent {
    color: var(--primary);
  }
  .subtitle {
    color: var(--text-muted);
    font-size: 1.05rem;
    max-width: 580px;
  }
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
    transition:
      border-color 0.15s,
      transform 0.15s;
  }
  .feature-card:hover {
    border-color: var(--primary);
    transform: translateY(-2px);
  }
  .feat-icon {
    color: var(--color-cobalt);
    display: flex;
    align-items: center;
  }
  .feature-card h3 {
    margin: 0;
    font-size: 1rem;
  }
  .feature-card p {
    color: var(--text-muted);
    font-size: 0.85rem;
    flex: 1;
    margin: 0;
  }
  .go-btn {
    color: var(--primary);
    font-size: 0.85rem;
    font-weight: 600;
  }
</style>

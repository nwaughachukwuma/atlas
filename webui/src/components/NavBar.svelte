<script>
  import {
    HouseIcon,
    MicIcon,
    FlaskConicalIcon,
    DatabaseIcon,
    FilmIcon,
    ClipboardListIcon,
    LayoutDashboardIcon,
    ZapIcon,
  } from "lucide-svelte";

  export let currentPath = "/";

  const links = [
    { path: "/", icon: HouseIcon, label: "Home", title: "Atlas Video" },
    {
      path: "/transcribe",
      icon: MicIcon,
      label: "Transcribe",
      title: "Transcribe",
    },
    {
      path: "/extract",
      icon: FlaskConicalIcon,
      label: "Extract",
      title: "Extract Insights",
    },
    {
      path: "/index",
      icon: DatabaseIcon,
      label: "Index",
      title: "Index Video",
    },
    {
      path: "/videos",
      icon: FilmIcon,
      label: "Videos",
      title: "Indexed Videos",
    },
    {
      path: "/queue",
      icon: ClipboardListIcon,
      label: "Queue",
      title: "Task Queue",
    },
    {
      path: "/dashboard",
      icon: LayoutDashboardIcon,
      label: "Dashboard",
      title: "Dashboard",
    },
  ];

  function isActive(path) {
    if (path === "/") return currentPath === "/";
    return currentPath.startsWith(path);
  }
</script>

<nav>
  <div class="logo">
    <a href="#/">
      <ZapIcon size={16} strokeWidth={2} />
      <span>Atlas</span>
    </a>
    <span class="version">Multimodal AI</span>
  </div>
  <ul>
    {#each links as l}
      <li class:active={isActive(l.path)}>
        <a href={`#${l.path}`}>
          <svelte:component this={l.icon} size={15} strokeWidth={1.5} />
          <span>{l.label}</span>
        </a>
      </li>
    {/each}
  </ul>
  <div class="nav-footer">
    <span class="muted">Atlas Multimodal Engine</span>
    <a
      href="https://github.com/nwaughachukwuma/atlas-video"
      target="_blank"
      class="gh-link">GitHub ↗</a
    >
  </div>
</nav>

<style>
  nav {
    width: 210px;
    min-height: 100vh;
    background: var(--color-surface);
    border-right: 1px solid var(--color-line);
    display: flex;
    flex-direction: column;
    padding: 1.25rem 0;
    position: sticky;
    top: 0;
    flex-shrink: 0;
  }
  .logo {
    padding: 0 1.1rem 1.25rem;
    border-bottom: 1px solid var(--color-line);
    margin-bottom: 0.75rem;
  }
  .logo a {
    font-family: var(--font-display);
    font-size: 1.15rem;
    font-weight: 900;
    color: var(--color-cobalt);
    display: flex;
    align-items: center;
    gap: 0.35rem;
    letter-spacing: -0.02em;
  }
  .version {
    font-size: 0.7rem;
    font-weight: 700;
    color: var(--color-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.2em;
  }
  ul {
    list-style: none;
    margin: 0;
    padding: 0;
    flex: 1;
  }
  li a {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.55em 1.1rem;
    color: var(--color-text-muted);
    font-size: 0.88rem;
    font-weight: 500;
    border-left: 2px solid transparent;
    transition: all 0.3s linear;
  }
  li a:hover {
    color: var(--color-text);
    background: var(--color-surface-alt);
  }
  li.active a {
    color: var(--color-cobalt);
    border-left-color: var(--color-cobalt);
    background: rgba(19, 81, 170, 0.06);
    font-weight: 700;
  }
  .nav-footer {
    padding: 1rem 1.1rem 0;
    border-top: 1px solid var(--color-line);
    font-size: 0.75rem;
    display: flex;
    flex-direction: column;
    gap: 0.3em;
  }
  .muted {
    color: var(--color-text-muted);
  }
  .gh-link {
    color: var(--color-text-muted);
  }
  .gh-link:hover {
    color: var(--color-cobalt);
  }
</style>

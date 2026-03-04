<script>
  import Router from "svelte-spa-router";
  import { location } from "svelte-spa-router";
  import NavBar from "./components/NavBar.svelte";
  import HowItWorks from "./components/HowItWorks.svelte";
  import Home from "./pages/Home.svelte";
  import Transcribe from "./pages/Transcribe.svelte";
  import Extract from "./pages/Extract.svelte";
  import Index from "./pages/Index.svelte";
  import Videos from "./pages/Videos.svelte";
  import VideoDetail from "./pages/VideoDetail.svelte";
  import Queue from "./pages/Queue.svelte";
  import Dashboard from "./pages/Dashboard.svelte";

  const routes = {
    "/": Home,
    "/transcribe": Transcribe,
    "/extract": Extract,
    "/index": Index,
    "/videos": Videos,
    "/videos/:id": VideoDetail,
    "/queue": Queue,
    "/queue/:id": Queue,
    "/dashboard": Dashboard,
  };

  let currentPath = "/";
  $: currentPath = $location;
</script>

<NavBar {currentPath} />
<main>
  <Router {routes} />
</main>

<div class="help-fixed">
  <HowItWorks />
</div>

<style>
  main {
    flex: 1;
    overflow-y: auto;
    min-height: 100vh;
  }
  .help-fixed {
    position: fixed;
    top: 1rem;
    right: 1.25rem;
    z-index: 100;
  }
</style>

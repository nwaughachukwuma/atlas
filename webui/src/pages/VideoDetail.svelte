<script lang="ts">
  import { route, type RouteResult } from "@mateothegreat/svelte5-router";
  import { FilmIcon, LoaderCircleIcon } from "lucide-svelte";
  import { onMount } from "svelte";
  import { getVideo, search } from "../lib/api.ts";
  import type { Video, SearchResult } from "../lib/types.ts";
  import ChatPanel from "../components/ChatPanel.svelte";
  import { toPath } from "../lib/routing.ts";
  import { toast } from "svelte-sonner";

  let { route: routeResult }: { route: RouteResult } = $props();

  // @ts-expect-error
  let videoId: string = $derived(routeResult.result.path.params?.id);
  let videoData = $state<Video | null>(null);
  let loading = $state(true);

  let searchQuery = $state("");
  let searchResults = $state<SearchResult[] | null>(null);
  let searching = $state(false);
  let pollInterval = $state<number | null>(null);
  let taskStatus = $state<string | null>(null);

  async function loadVideoData() {
    if (!videoId) throw new Error("videoId not found");
    return getVideo(videoId)
      .then((d) => {
        if (d.data) videoData = d.data;
        return d.data;
      })
      .catch((e) => {
        // may still be indexing via queue — poll
        if (e.message.includes("404") || e.message.includes("No data")) {
          taskStatus = "pending";
          return;
        }
        toast.error("Error fetching video data", { description: e.message });
      })
      .finally(() => (loading = false));
  }

  async function doSearch() {
    if (!searchQuery.trim()) {
      return (searchResults = null);
    }
    searching = true;
    return search(searchQuery.trim(), videoId, 10)
      .then((d) => (searchResults = d.results))
      .catch((e) =>
        toast.error("Error while searching video", {
          description: e.message,
        }),
      )
      .finally(() => (searching = false));
  }

  function clearSearch(): void {
    searchQuery = "";
    searchResults = null;
  }

  onMount(() => {
    loadVideoData();
    if (!videoData) {
      // Poll until video is available (queued indexing)
      pollInterval = setInterval(() => {
        loadVideoData().then(
          (d) => d && pollInterval && clearInterval(pollInterval),
        );
      }, 4000);
    }
    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  });
</script>

<div class="p-8 max-w-[860px]">
  <div class="mb-4 text-[0.85rem]">
    <a href={toPath("/videos")} use:route>← All Videos</a>
  </div>
  <h2>
    <FilmIcon
      size={20}
      strokeWidth={2}
      style="display:inline;vertical-align:middle;"
    /> Video Detail
  </h2>
  <code
    class="block text-[0.8rem] bg-surface-alt px-[0.5em] py-[0.25em] font-mono mt-1 mb-5 w-fit"
    >{videoId}</code
  >

  {#if loading}
    <div class="card flex items-center gap-x-2 text-center py-8">
      <LoaderCircleIcon
        class="w-5 h-5 animate-spin"
        style="animation-duration: 0.3s"
      />
      <span>Loading video data…</span>
    </div>
  {:else if !videoData}
    <div class="card py-8">
      <div class="flex items-center gap-x-2">
        <LoaderCircleIcon
          class="w-5 h-5 animate-spin"
          style="animation-duration: 0.3s"
        />
        <div>Video is being indexed...Checking every 4s.</div>
      </div>
      <p class="text-muted mt-4 text-[0.85rem] mb-0">
        This page will update automatically when ready.
      </p>
    </div>
  {:else}
    <div class="flex gap-2 mb-5">
      <input
        type="search"
        bind:value={searchQuery}
        placeholder="Search within this video…"
        class="flex-1"
        onkeydown={(e) => e.key === "Enter" && doSearch()}
      />
      <button
        class="btn-primary"
        onclick={doSearch}
        disabled={searching || !searchQuery.trim()}
      >
        {#if searching}
          <LoaderCircleIcon
            class="w-5 h-5 animate-spin"
            style="animation-duration: 0.3s"
          />
        {:else}Search{/if}
      </button>
      {#if searchResults !== null}
        <button class="btn-secondary" onclick={clearSearch}>Clear</button>
      {/if}
    </div>

    {#if searchResults !== null}
      <section class="card">
        <h3 class="mb-3">
          Search results <span class="text-muted text-[0.85rem]"
            >({searchResults.length})</span
          >
        </h3>
        {#if searchResults.length === 0}
          <p class="text-muted text-[0.85rem]">No results.</p>
        {:else}
          {#each searchResults as r}
            <div class="border-b border-line py-3 last:border-b-0">
              <span class="text-[0.75rem] text-muted"
                >score: {r.score?.toFixed(3) ?? "—"}</span
              >
              {#if r.description}
                <p class="text-[0.88rem] mt-1 mb-0">
                  {r.description}
                </p>
              {/if}
              {#if r.transcript}
                <p class="text-[0.85rem] text-muted mb-0">
                  {r.transcript}
                </p>
              {/if}
            </div>
          {/each}
        {/if}
      </section>
    {:else}
      <div class="card mb-4">
        <h3 class="mb-3">Video Info</h3>
        <div class="flex flex-col gap-[0.4rem]">
          {#each Object.entries(videoData) as [k, v]}
            {#if typeof v !== "object" || v === null}
              <div class="flex gap-4 text-[0.88rem]">
                <span class="text-muted min-w-32">{k}</span>
                <span class="text-ink">{v ?? "—"}</span>
              </div>
            {/if}
          {/each}
        </div>
        {#if videoData.chunks}
          <h4 class="mt-4">Segments ({videoData.chunks.length})</h4>
          {#each videoData.chunks as chunk, i (`${i}:${chunk.start_time}`)}
            <details class="border border-line mb-[0.4rem] p-[0.4rem]">
              <summary
                class="cursor-pointer text-[0.85rem] text-muted hover:text-cobalt"
                >Segment {i + 1}</summary
              >
              <pre>{JSON.stringify(chunk, null, 2)}</pre>
            </details>
          {/each}
        {/if}
      </div>
    {/if}
  {/if}
</div>

<ChatPanel {videoId} />

<script lang="ts" module>
  import type { VideoChunk } from "../lib/types.ts";
  type Props = {
    index: number;
    chunk: VideoChunk;
    open?: boolean;
    onClose: () => void;
  };
</script>

<script lang="ts">
  import { onMount } from "svelte";
  import { XIcon } from "lucide-svelte";
  import { formatTime } from "../lib/timing.ts";
  let { open = false, chunk, index, onClose }: Props = $props();

  let isOpen = $state(false);
  let startY = $state(0);
  let currentY = $state(0);
  let isDragging = $state(false);
  let sheetRef: HTMLDivElement | null = $state(null);

  $effect(() => {
    isOpen = open;
  });

  function close() {
    isOpen = false;
    onClose();
  }

  function handleTouchStart(e: TouchEvent) {
    isDragging = true;
    startY = e.touches[0].clientY;
    currentY = startY;
  }

  function handleTouchMove(e: TouchEvent) {
    if (!isDragging) return;

    const deltaY = e.touches[0].clientY - startY;
    if (deltaY > 0) {
      currentY = e.touches[0].clientY;
      if (sheetRef) {
        sheetRef.style.transform = `translateY(${Math.min(deltaY, 100)}px)`;
      }
    }
  }

  function handleTouchEnd() {
    if (!isDragging) return;

    isDragging = false;
    const deltaY = currentY - startY;
    if (deltaY > 50) {
      close();
    } else if (sheetRef) {
      sheetRef.style.transform = "translateY(0)";
    }
    currentY = 0;
  }

  function handleBackdropClick(e: MouseEvent | KeyboardEvent) {
    if (e.target === e.currentTarget) close();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Escape" && isOpen) close();
  }

  onMount(() => {
    document.addEventListener("keydown", handleKeydown);
    return () => {
      document.removeEventListener("keydown", handleKeydown);
    };
  });
</script>

{#if isOpen}
  <div
    role="dialog"
    aria-modal="true"
    tabindex="-1"
    class="fixed inset-0 z-50 flex items-end justify-center bg-ink/50 backdrop-blur-sm"
    onclick={handleBackdropClick}
    onkeydown={handleBackdropClick}
  >
    <div
      bind:this={sheetRef}
      class="bg-surface w-full max-w-4xl max-h-[94%] overflow-y-auto rounded-t-lg border-t border-line shadow-2xl transition-transform duration-200 ease-out"
      role="document"
      ontouchstart={handleTouchStart}
      ontouchmove={handleTouchMove}
      ontouchend={handleTouchEnd}
    >
      <!-- Drag handle -->
      <div
        class="sticky top-0 bg-surface z-10 border-b border-line px-6 py-3 flex items-center justify-between"
      >
        <div class="flex items-center gap-3">
          <div class="w-10 h-1 bg-line rounded-full"></div>
          {#if chunk}
            <span class="text-[0.85rem] text-muted font-mono">
              {formatTime(chunk.start)} - {formatTime(chunk.end)}
            </span>
            {#if index !== undefined}
              <span class="tag">Segment {index + 1}</span>
            {/if}
          {/if}
        </div>
        <button
          class="btn-secondary p-2 flex items-center justify-center"
          onclick={close}
          aria-label="Close"
        >
          <XIcon size={18} strokeWidth={2} />
        </button>
      </div>

      <!-- Content -->
      <div class="p-6">
        {#if chunk}
          {#if chunk.summary}
            <div class="mb-6 p-4 bg-surface-alt border border-line">
              <h3 class="text-[0.9rem] font-semibold mb-2">Summary</h3>
              <p class="text-[0.9rem] text-ink leading-relaxed mb-0">
                {chunk.summary}
              </p>
            </div>
          {/if}

          {#if chunk.video_analysis?.length}
            <div class="space-y-4">
              {#each chunk.video_analysis as v, i (`${i}:${v.attr}`)}
                {#if v.value}
                  <div class="mb-4 space-y-2">
                    <h4 class="capitalize text-muted">
                      {v.attr.split("_").join(" ")}
                    </h4>
                    <p class="text-sm text-ink leading-relaxed">
                      {v.value}
                    </p>
                  </div>
                {/if}
              {/each}
            </div>
          {/if}
        {:else}
          <p class="text-muted text-center py-8">No segment data available</p>
        {/if}
      </div>
    </div>
  </div>
{/if}

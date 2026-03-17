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
  import cs from "clsx";
  import { formatTime } from "../lib/timing.ts";

  let { open = false, chunk, index, onClose }: Props = $props();

  let isMounted = $state(false);
  let isOpen = $state(false);
  let startY = $state(0);
  let currentY = $state(0);
  let isDragging = $state(false);
  let sheetRef: HTMLDivElement | null = $state(null);

  $effect(() => {
    if (open) {
      isMounted = true;
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          isOpen = true;
        });
      });
    } else {
      isOpen = false;
    }
  });

  function close() {
    isOpen = false;
    setTimeout(() => {
      isMounted = false;
      onClose();
    }, 320);
  }

  function handleTouchStart(e: TouchEvent) {
    isDragging = true;
    startY = e.touches[0].clientY;
    currentY = startY;
    if (sheetRef) sheetRef.style.transition = "none";
  }

  function handleTouchMove(e: TouchEvent) {
    if (!isDragging) return;
    const deltaY = e.touches[0].clientY - startY;
    if (deltaY > 0) {
      currentY = e.touches[0].clientY;
      if (sheetRef)
        sheetRef.style.transform = `translateY(${Math.min(deltaY, 200)}px)`;
    }
  }

  function handleTouchEnd() {
    if (!isDragging) return;
    isDragging = false;
    const deltaY = currentY - startY;
    if (sheetRef) sheetRef.style.transition = "";
    if (deltaY > 80) {
      close();
    } else {
      if (sheetRef) sheetRef.style.transform = "";
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
    return () => document.removeEventListener("keydown", handleKeydown);
  });
</script>

{#if isMounted}
  <div
    role="dialog"
    aria-modal="true"
    tabindex="-1"
    class={cs(
      "fixed inset-0 z-50 flex items-end justify-center transition-[background-color,backdrop-filter] duration-300 ease-out",
      isOpen ? "bg-ink/50 backdrop-blur-sm" : "bg-transparent",
    )}
    onclick={handleBackdropClick}
    onkeydown={handleBackdropClick}
  >
    <div
      bind:this={sheetRef}
      class="bg-surface w-full max-w-4xl max-h-[94%] overflow-y-auto rounded-t-lg border-t border-line shadow-2xl transition-transform duration-300 ease-[cubic-bezier(0.32,0.72,0,1)] will-change-transform"
      class:translate-y-0={isOpen}
      class:translate-y-full={!isOpen}
      role="document"
      ontouchstart={handleTouchStart}
      ontouchmove={handleTouchMove}
      ontouchend={handleTouchEnd}
    >
      <!-- Header -->
      <div
        class="sticky top-0 bg-surface z-10 border-b border-line px-5 pt-3 pb-3"
      >
        <!-- Drag pill -->
        <div class="flex justify-center mb-3">
          <div class="w-9 h-1 rounded-full bg-line opacity-70"></div>
        </div>
        <!-- Meta row -->
        <div class="flex items-center justify-between gap-3">
          <div class="flex items-center gap-2.5 min-w-0">
            {#if index !== undefined}
              <span class="tag shrink-0">Segment {index + 1}</span>
            {/if}
            {#if chunk}
              <span class="text-[0.8rem] text-muted font-mono truncate">
                {formatTime(chunk.start)} — {formatTime(chunk.end)}
              </span>
            {/if}
          </div>
          <button
            class="btn-secondary p-1.5 flex items-center justify-center shrink-0"
            onclick={close}
            aria-label="Close"
          >
            <XIcon size={16} strokeWidth={2} />
          </button>
        </div>
      </div>

      <!-- Body -->
      <div class="p-5 space-y-3">
        {#if chunk}
          {#if chunk.summary}
            <div
              class="p-4 bg-surface-alt border border-line border-l-[3px] border-l-cobalt"
            >
              <p
                class="text-[0.7rem] uppercase tracking-widest text-muted font-semibold mb-2"
              >
                Summary
              </p>
              <p class="text-[0.9rem] text-ink leading-relaxed">
                {chunk.summary}
              </p>
            </div>
          {/if}

          {#if chunk.video_analysis?.length}
            <div class="grid gap-2.5">
              {#each chunk.video_analysis as v, i (`${i}:${v.attr}`)}
                {#if v.value}
                  <div class="p-4 border border-line bg-surface-alt">
                    <p
                      class="text-[0.7rem] uppercase tracking-widest text-muted font-semibold mb-1.5"
                    >
                      {v.attr.split("_").join(" ")}
                    </p>
                    <p class="text-[0.875rem] text-ink leading-relaxed">
                      {v.value}
                    </p>
                  </div>
                {/if}
              {/each}
            </div>
          {/if}
        {:else}
          <p class="text-muted text-center py-12 text-sm">
            No segment data available
          </p>
        {/if}
      </div>
    </div>
  </div>
{/if}

<script lang="ts" module>
  import { formatTime } from "../lib/timing.ts";
  import type { VideoChunk, DescriptionAttr } from "../lib/types.ts";
  type Props = {
    chunks?: VideoChunk[];
    onSegmentClick: (chunk: VideoChunk, index: number) => void;
  };
</script>

<script lang="ts">
  let { chunks = [], onSegmentClick }: Props = $props();

  function getPreviewText(chunk: VideoChunk): string {
    if (chunk.summary) return chunk.summary;

    const priorityAttrs: DescriptionAttr[] = [
      "visual_cues",
      "transcript",
      "audio_analysis",
      "contextual_information",
      "interactions",
    ];

    for (const attr of priorityAttrs) {
      const found = chunk.video_analysis?.find((v) => v.attr === attr);
      if (found) return found.value.trim();
    }
    return "No preview available";
  }
</script>

{#if !chunks.length}
  <div class="card py-8 text-center text-muted">
    <p class="mb-0">No segments available</p>
  </div>
{:else}
  <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
    {#each chunks as c, i (`${i}:${c.start}:${c.end}`)}
      <button
        class="card text-left hover:border-cobalt transition-colors cursor-pointer h-full flex flex-col"
        onclick={() => onSegmentClick(c, i)}
      >
        <div class="flex items-center gap-2 mb-2 text-[0.75rem] text-muted">
          <span class="font-mono bg-surface-alt px-2 py-0.5 rounded">
            {formatTime(c.start)} - {formatTime(c.end)}
          </span>
        </div>

        <p class="text-[0.85rem] text-ink-2 font-normal line-clamp-5 flex-1">
          {getPreviewText(c)}
        </p>

        {#if c.video_analysis}
          <div
            class="mt-3 pt-3 border-t border-line flex items-center gap-2 text-[0.75rem] text-muted"
          >
            {#each c.video_analysis.slice(0, 2) as v, i (i)}
              {#if i < 3}
                <span class="tag text-xs font-normal">{v.attr}</span>
              {/if}
            {/each}

            {#if !!c.video_analysis.slice(2).length}
              <span class="tag">
                +{c.video_analysis.length - 2}
              </span>
            {/if}
          </div>
        {/if}
      </button>
    {/each}
  </div>
{/if}

<script lang="ts" module>
  type Props = { text: string; title?: string };
</script>

<script lang="ts">
  import { CopyIcon, CheckIcon } from "lucide-svelte";
  let { text = "", title = "Copy to clipboard" }: Props = $props();
  let copied = $state(false);

  async function copy() {
    if (!text) return;
    await navigator.clipboard.writeText(text);
    copied = true;
    setTimeout(() => (copied = false), 1500);
  }
</script>

<button
  class="inline-flex items-center gap-1 text-muted hover:text-cobalt text-[0.78rem] cursor-pointer bg-transparent border-0 p-0"
  onclick={copy}
  {title}
>
  {#if copied}
    <CheckIcon size={14} strokeWidth={2} /> Copied
  {:else}
    <CopyIcon size={14} strokeWidth={2} /> Copy
  {/if}
</button>

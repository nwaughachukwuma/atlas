/** Atlas API client – all calls go to the same origin. */

const BASE = '';

async function post(path, body) {
  const res = await fetch(BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ? JSON.stringify(err.detail) : res.statusText);
  }
  return res.json();
}

async function postForm(path, formData) {
  const res = await fetch(BASE + path, { method: 'POST', body: formData });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ? JSON.stringify(err.detail) : res.statusText);
  }
  return res.json();
}

async function get(path) {
  const res = await fetch(BASE + path);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ? JSON.stringify(err.detail) : res.statusText);
  }
  return res.json();
}

// ── Mutating endpoints ────────────────────────────────────────────────────────

export function transcribe(file, opts = {}) {
  const fd = new FormData();
  fd.append('video', file);
  fd.append('format', opts.format ?? 'text');
  fd.append('benchmark', String(opts.benchmark ?? false));
  fd.append('no_queue', String(opts.no_queue ?? true));
  fd.append('no_streaming', String(opts.no_streaming ?? true));
  if (opts.output) fd.append('output', opts.output);
  return postForm('/transcribe', fd);
}

export function extract(file, opts = {}) {
  const fd = new FormData();
  fd.append('video', file);
  fd.append('chunk_duration', opts.chunk_duration ?? '15s');
  fd.append('overlap', opts.overlap ?? '1s');
  fd.append('format', opts.format ?? 'json');
  fd.append('include_summary', String(opts.include_summary ?? true));
  fd.append('benchmark', String(opts.benchmark ?? false));
  fd.append('no_queue', String(opts.no_queue ?? true));
  fd.append('no_streaming', String(opts.no_streaming ?? true));
  if (opts.attrs) fd.append('attrs', opts.attrs);
  if (opts.output) fd.append('output', opts.output);
  return postForm('/extract', fd);
}

export function indexVideo(file, opts = {}) {
  const fd = new FormData();
  fd.append('video', file);
  fd.append('chunk_duration', opts.chunk_duration ?? '15s');
  fd.append('overlap', opts.overlap ?? '1s');
  fd.append('include_summary', String(opts.include_summary ?? true));
  fd.append('benchmark', String(opts.benchmark ?? false));
  fd.append('no_queue', String(opts.no_queue ?? true));
  fd.append('no_streaming', String(opts.no_streaming ?? true));
  if (opts.attrs) fd.append('attrs', opts.attrs);
  return postForm('/index', fd);
}

// ── Read-only endpoints ───────────────────────────────────────────────────────

export const search = (query, video_id = null, top_k = 10) =>
  post('/search', { query, video_id, top_k });

export const listVideos = () => get('/list-videos');
export const getVideo = (id) => get(`/get-video/${id}`);
export const listChat = (id, last_n = 50) => get(`/list-chat/${id}?last_n=${last_n}`);
export const stats = () => get('/stats');
export const health = () => get('/health');
export const queueList = (status = null) =>
  get('/queue/list' + (status ? `?status=${status}` : ''));
export const queueStatus = (id) => get(`/queue/status/${id}`);

// ── SSE chat stream ───────────────────────────────────────────────────────────

/**
 * Stream a chat response for the given video.
 * @param {string} videoId
 * @param {string} query
 * @param {(chunk: string) => void} onChunk  called for each SSE data chunk
 * @param {() => void} onDone               called when the stream ends
 * @returns {AbortController}  call .abort() to cancel early
 */
export function chatStream(videoId, query, onChunk, onDone) {
  const ctrl = new AbortController();
  fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ video_id: videoId, query }),
    signal: ctrl.signal,
  }).then(async (res) => {
    if (!res.ok) throw new Error(await res.text());
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const lines = buf.split('\n');
      buf = lines.pop();
      for (const line of lines) {
        if (line.startsWith('data: ')) onChunk(line.slice(6));
      }
    }
    onDone();
  }).catch((err) => {
    if (err.name !== 'AbortError') onChunk(`\n[Error: ${err.message}]`);
    onDone();
  });
  return ctrl;
}

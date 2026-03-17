export function formatTime(time: string | number | undefined): string {
  if (time === undefined) return "0:00";
  const seconds = typeof time === "string" ? parseFloat(time) : time;
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}

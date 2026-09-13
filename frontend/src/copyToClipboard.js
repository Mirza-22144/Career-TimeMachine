// Selects and copies text via the older execCommand approach. Used when
// navigator.clipboard is unavailable or blocked (e.g. no clipboard-write
// permission, an insecure context, or an older browser) - the modern API
// alone can silently fail in exactly those cases with no fallback.
function copyWithFallback(text) {
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "");
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  textarea.setSelectionRange(0, text.length);
  const succeeded = document.execCommand("copy");
  document.body.removeChild(textarea);
  if (!succeeded) throw new Error("execCommand copy failed");
}

// Tries the modern Clipboard API first, falls back to the older
// execCommand approach if that is unavailable or fails. Throws only if
// both methods fail, so callers can show a manual-copy message.
export async function copyToClipboard(text) {
  try {
    if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      return;
    }
  } catch {
    // fall through to the execCommand fallback below
  }
  copyWithFallback(text);
}

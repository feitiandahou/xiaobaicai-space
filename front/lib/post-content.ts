function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function normalizePastedHtml(value: string): string {
  const trimmed = value.trim();
  if (!trimmed) {
    return '';
  }

  const bodyMatch = /<body[^>]*>([\s\S]*?)<\/body>/i.exec(trimmed);
  const content = bodyMatch?.[1] ?? trimmed;

  return content
    .replace(/<\/?(?:html|head|body)[^>]*>/gi, '')
    .replace(/<!--([\s\S]*?)-->/g, '')
    .trim();
}

function hasHtmlStructure(value: string): boolean {
  return /<\/?[a-z][\s\S]*>/i.test(value);
}

export function handleRichTextPaste(
  event: React.ClipboardEvent<HTMLTextAreaElement>,
  value: string,
  onChange: (nextValue: string) => void,
): void {
  const html = normalizePastedHtml(event.clipboardData.getData('text/html'));
  if (!html) {
    return;
  }

  event.preventDefault();

  const target = event.currentTarget;
  const start = target.selectionStart ?? value.length;
  const end = target.selectionEnd ?? value.length;
  const nextValue = `${value.slice(0, start)}${html}${value.slice(end)}`;
  const nextCursor = start + html.length;

  onChange(nextValue);

  requestAnimationFrame(() => {
    target.selectionStart = nextCursor;
    target.selectionEnd = nextCursor;
  });
}

export function toRenderablePostHtml(content: string): string {
  if (!content.trim()) {
    return '';
  }

  if (hasHtmlStructure(content)) {
    return content;
  }

  return content
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean)
    .map((paragraph) => `<p>${escapeHtml(paragraph).replace(/\n/g, '<br />')}</p>`)
    .join('');
}
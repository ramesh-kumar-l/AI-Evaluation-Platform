/**
 * Accessibility: skip-nav link visible only on keyboard focus.
 * Place at the top of the page layout so keyboard users can bypass navigation.
 */
export function SkipToContent({ targetId = "main-content" }: { targetId?: string }) {
  return (
    <a
      href={`#${targetId}`}
      className={[
        "sr-only focus:not-sr-only",
        "focus:fixed focus:top-2 focus:left-2 focus:z-50",
        "focus:rounded focus:bg-indigo-600 focus:px-4 focus:py-2",
        "focus:text-white focus:text-sm focus:font-medium focus:shadow-lg",
        "focus:outline-none focus:ring-2 focus:ring-white",
      ].join(" ")}
    >
      Skip to main content
    </a>
  );
}

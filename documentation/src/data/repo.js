/**
 * The repository, and links into it.
 *
 * `issueUrl` was a private function in at-scale.js and is now needed on the roadmap page too,
 * so it lives here rather than being copied. The repository URL was also written out by hand in
 * several places; a constant means a rename or a move is one edit.
 */

export const REPO = 'https://github.com/StackGuardian/tirith';

/** The template picker: three templates, and the reader chooses. */
export const NEW_ISSUE = `${REPO}/issues/new/choose`;

/**
 * A link to one issue template, optionally with the title prefilled.
 *
 * Prefer this over the `/choose` picker whenever the button names the thing it opens. A control
 * reading "Request a feature" that lands on a menu of three templates has broken its promise, and
 * the reader now has to work out which of them you meant.
 *
 * Templates that exist in .github/ISSUE_TEMPLATE/ (the filename is the parameter):
 *   feature_request.md   labels: enhancement, title prefixed 🚀
 *   bug_report.md        labels: bug
 *   general-issue.md     no labels
 *
 * Naming a template that does not exist is not an error GitHub reports: it silently falls back to
 * a blank issue form, so the labels quietly stop being applied. Check the directory before
 * inventing a value here.
 */
export function issueUrl({template = 'general-issue.md', title} = {}) {
  const params = new URLSearchParams({template});
  if (title) params.set('title', title);
  return `${REPO}/issues/new?${params.toString()}`;
}

import {useEffect} from 'react';

/**
 * The one place the landing page talks to analytics.
 *
 * Every call goes through capture() rather than touching window.posthog
 * directly, so that:
 *
 *   - a page with no key configured is silent rather than broken. PostHog is
 *     only loaded when POSTHOG_KEY is set at build time (see
 *     src/clientModules/posthog.js), which it is not for a local `docusaurus
 *     start`, a fork's build, or anyone running the docs offline;
 *   - the event vocabulary is auditable from a single file. The properties
 *     below are deliberately coarse -- a CI system name, a mode, a stage.
 *     Nothing here may carry a repository name, a plan, policy text, source
 *     code or a token, because this is a public page and none of that is ours
 *     to collect.
 *
 * Tirith's own local mode is unrelated to any of this and stays networkless.
 *
 * NOTE: this file is no longer byte-identical to documentation/src/analytics.js. The
 * `fleet_*` events were renamed to `at_scale_*` when the page was renamed, and the older
 * site still uses the old names. Reconcile them when that site is retired.
 */

export const EVENTS = {
  // Landing
  heroStar: 'hero_star_click',
  quickstart: 'quickstart_click',
  installCopy: 'install_copy',
  demoPr: 'demo_pr_open',
  policyExample: 'policy_example_open',
  firstPlan: 'first_plan_self_report',
  helpIssue: 'help_issue_open',
  platformInterest: 'platform_interest',

  // Learn
  learnStart: 'learn_start',
  lessonStart: 'lesson_start',
  lessonComplete: 'lesson_complete',
  courseComplete: 'course_complete',
  learnToPlayground: 'learn_to_playground',
  learnToQuickstart: 'learn_to_quickstart',

  // Playground
  playgroundOpen: 'playground_open',
  fixtureSelect: 'fixture_select',
  templateSelect: 'template_select',
  evaluationRun: 'evaluation_run',
  evaluationOutcome: 'evaluation_outcome',
  policyExport: 'policy_export',
  snippetCopy: 'snippet_copy',
  playgroundToRepo: 'playground_to_repo',
  playgroundToScale: 'playground_to_at_scale',
  // Not in the brief's list: the builder became a tab on this page, and a tab
  // nobody opens is worth knowing about.
  builderOpen: 'builder_open',

  // At scale
  scaleView: 'at_scale_view',
  offerCta: 'offer_cta_click',
  scaleCapabilityExpand: 'at_scale_capability_expand',
  scaleFormStart: 'at_scale_form_start',
  scaleFormSubmit: 'at_scale_form_submit',
  scaleToOss: 'at_scale_to_oss',

  // AI
  aiView: 'ai_view',
  skillCopy: 'skill_file_copy',
  // Kept under its old name so any dashboard already built on it keeps working; it now
  // measures interest in estate-wide governance from the AI page rather than in an MCP server.
  sgMcpInterest: 'sg_mcp_interest',

  // Traction
  tractionView: 'traction_view',
  metricSourceOpen: 'metric_source_open',
  starFromTraction: 'star_from_traction',
  adopterIssueOpen: 'adopter_issue_open',
  contributionCta: 'contribution_cta_click',
};

export function capture(event, properties = {}) {
  if (typeof window === 'undefined') return;
  const posthog = window.posthog;
  if (!posthog || typeof posthog.capture !== 'function') return;
  try {
    posthog.capture(event, properties);
  } catch {
    // Analytics must never take the page down with it.
  }
}

/**
 * Returns an onClick handler. Written as a factory because nearly every call
 * site is a link whose only job is to fire one event and then behave like a
 * link -- no preventDefault, no navigation of its own.
 */
export function track(event, properties) {
  return () => capture(event, properties);
}

/**
 * Fire once when a page mounts. Written as a hook so a page can say what it is
 * in one line, and so the effect's empty dependency list lives in exactly one
 * place rather than being re-derived (and occasionally got wrong) per page.
 */
export function usePageView(event, properties) {
  useEffect(() => {
    capture(event, properties);
    // Mount only: a page view is not re-fired when props change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}

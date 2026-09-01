/**
 * What is being built, taken from the internal roadmap.
 *
 * Selection rule: a question a per-resource scanner cannot ask, or a gap that stops
 * someone adopting Tirith today. Everything on the internal plan that is table stakes,
 * hygiene, or an integration was left off. This is not the whole roadmap and does not
 * pretend to be.
 *
 * Status is two values and they mean different things.
 *
 *   inDev   there is code. `tirith lint` runs today outside the released package; the
 *           clearer result messages are an open pull request.
 *   planned specified, sized, ordered, and not started. Most of this list.
 *
 * Nothing here is shipped. Anything shipped belongs in the documentation instead, and the
 * moment one of these lands it should move out of this file rather than change status to a
 * third value, so the page cannot fill up with things that are already true.
 *
 * Dates are the internal plan's own estimates, relative and deliberately coarse. They are
 * the honest form of a roadmap date: an order and a rough distance, not a promise.
 */

export const RELEASES = [
  {
    id: 'verdict',
    n: '01',
    name: 'Trust the verdict',
    when: 'Next, about a month',
    lede:
      'Nothing new is worth building on an engine that can drop a result. This release is ' +
      'about the verdict itself being something you can rely on, and it changes verdicts, ' +
      'so it ships saying so.',
    items: [
      {
        title: 'A skipped check can never read as a pass',
        status: 'inDev',
        body:
          'A rule that could not run is already reported as unevaluated rather than as ' +
          'success, which nothing else in this category does. A defect in the rollup makes ' +
          'that untrue in some orderings, and it is measured: it changes the verdict on 327 ' +
          'policies. Fixing it is the first thing in the plan for a reason.',
      },
      {
        title: 'Fail on severity, not on everything',
        status: 'planned',
        body:
          'Every policy already carries a severity and nothing reads it. ' +
          '--fail-on-severity turns "block on critical, warn on medium" into one flag ' +
          'instead of four pipelines.',
      },
      {
        title: 'Blast radius as one rule',
        status: 'planned',
        body:
          '"Does this change delete more than two things?" is a property of the change, so ' +
          'a per-resource rule has nowhere to put it. Counting destroys becomes a single ' +
          'policy once count can filter on the action.',
      },
      {
        title: 'tirith test',
        status: 'planned',
        body:
          'A fixture convention and a runner, so a policy ships with proof that it fails on ' +
          'the document it is supposed to fail on. Every comparable tool can test its ' +
          'policies and Tirith cannot, which is backwards for a project asking strangers to ' +
          'contribute rules.',
      },
      {
        title: 'Failures that name the resource',
        status: 'inDev',
        body:
          'Every result says which resource address, which planned action and which ' +
          'attribute produced it, so a red pipeline points at a line rather than a policy id.',
      },
    ],
  },

  {
    id: 'adopt',
    n: '02',
    name: 'Scope it, test it, package it',
    when: 'After that, about two months',
    lede:
      'The release that makes Tirith adoptable without writing every rule yourself, and ' +
      'safe for other people to contribute rules to.',
    items: [
      {
        title: 'Import the rules you already have',
        // The title no longer leads with another tool's name. The body still names it,
        // because the measurement is the point and a number without its source is a boast.
        status: 'planned',
        body:
          'A translation corpus of 2,495 upstream rules already exists, drawn from Checkov ' +
          'and three Powerpipe Terraform modules: 1,842 of them run as Tirith policies today ' +
          'and 653 do not, each with the reason recorded. Publishing them as installable ' +
          'packs, with a mapping table from the original check id, turns a rule-count gap ' +
          'into a migration path.',
      },
      {
        title: 'Policy packs and a default library',
        status: 'planned',
        body:
          'A manifest that selects a subset of policies and tags them, so "run the CIS pack ' +
          'at high and above" is one command. With a curated default set behind it, ' +
          'evaluating a plan works before you have written anything.',
      },
      {
        title: 'Policies from git',
        status: 'planned',
        body:
          'Point -policy-path at a git URL and pin it to a tag, the same way you already ' +
          'pin a Terraform module. Four teams share one rule set without anyone hosting a ' +
          'registry.',
      },
      {
        title: 'SARIF output',
        status: 'planned',
        body:
          'The verdict in the format GitHub code scanning, GitLab and most security ' +
          'dashboards already read, so the result lands where your other findings live.',
      },
    ],
  },

  {
    id: 'change',
    n: '03',
    name: 'Policy on the change',
    when: 'Then, about two months',
    lede:
      'Every item here is a question a per-resource engine cannot ask, because the subject ' +
      'is the change rather than any single resource in it.',
    items: [
      {
        title: 'Before and after, not just after',
        status: 'planned',
        body:
          'Reading the value a change moves from as well as the value it moves to makes the ' +
          'transition itself the subject of a rule. Deletion protection being switched off, ' +
          'a CIDR being widened, a retention window being cut. Today a policy sees only the ' +
          'new value, and on a delete it sees nothing at all.',
      },
      {
        title: 'Why a resource is being replaced',
        status: 'planned',
        body:
          'The plan already records the reason. Exposing it separates "you removed the ' +
          'module" from "you changed an immutable field", which are the same red diff and ' +
          'two different conversations.',
      },
      {
        title: 'Rules that know whose module it is',
        status: 'planned',
        body:
          'Filtering by module address routes a failure to the team that owns it, and turns ' +
          'blast radius per module into a rule rather than a spreadsheet.',
      },
      {
        title: 'Secrets, checked properly',
        status: 'planned',
        body:
          'The plan marks which values are sensitive. Reading that is the correct version of ' +
          '"secrets must be marked sensitive", which cannot be written honestly without it.',
      },
    ],
  },

  {
    id: 'layer',
    n: '04',
    name: 'The layer',
    when: 'Later, about three months',
    lede:
      'Provenance and correlation. These are the two things no comparable tool answers at ' +
      'all, which is why they are last: they are worth doing properly rather than early.',
    items: [
      {
        title: 'The plan being applied is the plan that was approved',
        status: 'planned',
        body:
          'A hash of the evaluated plan in the verdict, and a verify step in the apply job ' +
          'that refuses a plan it has not seen approved. Nothing else in this category ' +
          'answers this, because answering it means being present at two moments rather ' +
          'than one.',
      },
      {
        title: 'One rule across two documents',
        status: 'planned',
        body:
          'Naming several inputs at once lets a rule say "the scanner flagged this resource ' +
          'and the plan replaces it". Today a policy reads one document per run, so ' +
          'governing several tools means reconciling their output by hand.',
      },
      {
        title: 'Your own providers and conditions',
        status: 'planned',
        body:
          'A plugin interface for document readers and condition types, so a shape nobody ' +
          'here has thought of does not require a fork. Policies stay data: a plugin adds ' +
          'typed operations, not an escape hatch into code.',
      },
      {
        title: 'Installed the way you install anything else',
        status: 'planned',
        body:
          'Homebrew, a container image, a dev container feature, a pre-commit hook, and the ' +
          'Action listed on the Marketplace. Today installation is a git URL, which is the ' +
          'single most friction-heavy thing about starting.',
      },
    ],
  },
];

/**
 * The four the landing page shows. Kept short deliberately: the home page states that
 * work is happening and points here, rather than reproducing this list.
 *
 * Each id must match an item title above, so the two cannot drift apart silently.
 */
export const HIGHLIGHTS = [
  {
    title: 'Blast radius as one rule',
    status: 'planned',
    body: 'Count what a change destroys, not what each resource looks like.',
  },
  {
    title: 'Before and after, not just after',
    status: 'planned',
    body: 'Make the transition the subject: deletion protection switched off, a CIDR widened.',
  },
  {
    title: 'Applied plan equals approved plan',
    status: 'planned',
    body: 'A verify step that refuses a plan it has not seen approved.',
  },
  {
    // The only one of the four with code behind it, so the strip is not four planned
    // things in a row, and it is the row of the comparison table that no other tool in
    // this category answers at all.
    title: 'A skipped check can never read as a pass',
    status: 'inDev',
    body: 'A rule that could not run is reported as unevaluated, never as success.',
  },
];

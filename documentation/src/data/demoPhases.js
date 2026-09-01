/**
 * The five chapters every demo repository follows, and the repositories themselves.
 *
 * Keep this data static: the landing page must stay deterministic and must not depend on
 * any forge's API being reachable. Every outcome below is copied from a real run.
 *
 * The chapters are written platform-neutrally because all three demos follow them. Links
 * point at repository roots rather than individual pull requests or branches -- the demos
 * are maintained independently, and a deep link into one of them is stale the moment it is
 * rebased. `DEMO_REPOS` below carries the per-platform wiring instead.
 */
export const DEMO_PHASES = [
  {
    number: '01',
    group: 'Adopt · local',
    title: 'Add Tirith with local policies',
    summary: 'Keep the policies with the code and check every plan before apply.',
    body:
      'The first change adds three policy files and one pipeline step. Evaluation happens ' +
      'on your own runner, against policies committed beside the code.',
    delta: '4 files · +83',
    tag: 'Local policies',
    code: `permissions:
  pull-requests: write
  checks: write

- run: terraform show -json tfplan > plan.json
- uses: StackGuardian/tirith-iac-governance-action@v2
  with:
    fail-on-error: true`,
    outcome: {
      tone: 'pass',
      label: 'Real PR result',
      title: '3 passed',
      items: [
        'AWS provider is configured for us-east-1',
        'Every S3 bucket name starts with demo-',
        'Every S3 bucket declares an Owner tag',
      ],
      note: 'Tirith runs before Apply and posts the result as a check and pull-request comment.',
    },
    prUrl: 'https://github.com/StackGuardian/tirith-action-demo/pull/6',
    reportUrl:
      'https://github.com/StackGuardian/tirith-action-demo/pull/6#issuecomment-5394217543',
  },
  {
    number: '02',
    group: 'Scale · organization',
    title: 'Share policies across repositories',
    summary: 'Add organization credentials and select centrally managed policies.',
    body:
      'The pipeline step stays in the same place and reads the same plan. Adding two credentials ' +
      'moves policy selection, pricing, and run history to StackGuardian; the local policy ' +
      'files are removed.',
    delta: '4 files · +5 −77',
    tag: 'Optional platform',
    code: `- uses: StackGuardian/tirith-iac-governance-action@v2
  with:
    sg-api-key: \${{ secrets.SG_API_TOKEN }}
    sg-org: \${{ vars.SG_ORG }}
    fail-on-error: true

# .tirith/policies/*.json are removed`,
    outcome: {
      tone: 'warn',
      label: 'Real PR result',
      title: '1 warned · 3 passed',
      items: [
        'Infracost checked the estimated monthly cost',
        'OPA and Tirith policies passed',
        'Checkov reported advisory S3 findings',
      ],
      note: 'This phase requires a StackGuardian account; local mode remains fully usable without one.',
    },
    prUrl: 'https://github.com/StackGuardian/tirith-action-demo/pull/7',
    reportUrl:
      'https://github.com/StackGuardian/tirith-action-demo/pull/7#issuecomment-5394260017',
  },
  {
    number: '03',
    group: 'Enforce · fail',
    title: 'Add an empty Owner tag',
    summary: 'Only the Terraform changes. The existing gate catches the mistake.',
    body:
      'A new analytics bucket follows the naming rule but leaves Owner empty. The workflow ' +
      'and policies do not change: Tirith catches the problem with the gate that is already ' +
      'in place.',
    delta: '1 file · +10',
    tag: 'Apply blocked',
    code: `resource "aws_s3_bucket" "analytics" {
  bucket = "demo-tirith-action-analytics-790543352839"

  tags = {
    Name  = "tirith-action-demo"
    Demo  = "tirith-action-demo"
    Owner = ""
  }
}`,
    outcome: {
      tone: 'fail',
      label: 'Real PR result',
      title: '1 failed · 1 warned · 2 passed',
      items: [
        'The Owner policy failed on aws_s3_bucket.analytics',
        'The empty value is named in the report',
        'The Terraform job failed before Apply',
      ],
      note: 'The only code change is the ten-line bucket resource shown above.',
    },
    prUrl: 'https://github.com/StackGuardian/tirith-action-demo/pull/8',
    reportUrl:
      'https://github.com/StackGuardian/tirith-action-demo/pull/8#issuecomment-5394348514',
  },
  {
    number: '04',
    group: 'Enforce · recover',
    title: 'Fix one line and pass',
    summary: 'Give Owner a value and the same policy clears the change.',
    body:
      'The fix happens where the problem started: in Terraform. The pull request reruns, ' +
      'the same policy passes, and the pipeline can continue after merge.',
    delta: '1 file · +1 −1',
    tag: 'Gate clear',
    code: `tags = {
  Name  = "tirith-action-demo"
  Demo  = "tirith-action-demo"
- Owner = ""
+ Owner = "data-platform"
}`,
    outcome: {
      tone: 'pass',
      label: 'Real PR result',
      title: '1 warned · 3 passed',
      items: [
        'The Owner policy now passes',
        'The advisory Checkov warning remains visible',
        'The gate is clear for a main-branch apply',
      ],
      note: 'Pull-request runs skip Apply; the successful check lets the merged run proceed.',
    },
    prUrl: 'https://github.com/StackGuardian/tirith-action-demo/pull/9',
    reportUrl:
      'https://github.com/StackGuardian/tirith-action-demo/pull/9#issuecomment-5394354305',
  },
  {
    number: '05',
    group: 'Close the loop',
    title: 'Publish state after apply',
    summary: 'Send the current state without creating another policy verdict.',
    body:
      'The plan check decides whether a change can proceed. This final call only publishes ' +
      'the current Terraform state to StackGuardian. It stays silent and cannot block deployment.',
    delta: '2 files · +23',
    tag: 'Post-apply',
    code: `- run: terraform show -json > state.json

- uses: StackGuardian/tirith-iac-governance-action@v2
  continue-on-error: true
  with:
    input-path: state.json
    input-kind: terraform_state
    comment: false
    check: false
    comment-tag: post-apply`,
    outcome: {
      tone: 'neutral',
      label: 'Publication behavior',
      title: 'One gate. No duplicate report.',
      items: [
        'State is masked on the runner before upload',
        'The publication call creates no comment or check run',
        'A publication problem cannot fail the deployment',
      ],
      note: 'The tag keeps the uploaded state separate from the earlier plan bundle.',
    },
    prUrl: 'https://github.com/StackGuardian/tirith-action-demo/pull/10',
    reportUrl:
      'https://github.com/StackGuardian/tirith-action-demo/pull/10#issuecomment-5394358374',
  },
];


/**
 * Where each chapter has actually been played out. Roots only, deliberately.
 *
 * What differs between them is only how Tirith is invoked; the policies, the verdicts and
 * the exit codes are identical, because it is the same CLI underneath in every case.
 */
/**
 * Everywhere the gate can be wired up, for the switcher in section 03.
 *
 * Separate from DEMO_REPOS on purpose. Two of these -- a generic CI runner and a laptop --
 * have no repository to link to, and PhaseJourney maps DEMO_REPOS straight into links, so
 * merging the two lists would put dead links under every chapter of the walkthrough.
 *
 * `url` is an external demo repository; `to` is an internal docs route. An entry has one or
 * the other, never both.
 */
export const PIPELINE_TARGETS = [
  {
    id: 'github',
    name: 'GitHub Actions',
    file: '.github/workflows/plan.yml',
    note: 'The Action wraps the CLI and adds the pull-request comment and check run.',
    url: 'https://github.com/StackGuardian/tirith-action-demo',
    linkLabel: 'Open the GitHub demo',
    code: `permissions:
  contents: read
  pull-requests: write
  checks: write

steps:
  - run: |
      terraform plan -out=tfplan -input=false
      terraform show -json tfplan > plan.json

  - uses: StackGuardian/tirith-iac-governance-action@v2
    with:
      fail-on-error: true`,
  },
  {
    id: 'gitlab',
    name: 'GitLab CI',
    file: '.gitlab-ci.yml',
    note: 'No wrapper — the CLI directly, consuming the plan as an artifact.',
    url: 'https://gitlab.com/stackguardian/tirith-component-demo',
    linkLabel: 'Open the GitLab demo',
    code: `terraform-plan:
  stage: plan
  script:
    - terraform plan -out=tfplan -input=false
    - terraform show -json tfplan > plan.json
  artifacts: {paths: [plan.json]}

tirith:
  stage: policy
  image: python:3.12
  needs: [terraform-plan]
  script:
    - pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
    # - tirith lint .tirith/policies   # in dev, not in 1.2.0
    - tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error`,
  },
  {
    id: 'bitbucket',
    name: 'Bitbucket Pipelines',
    file: 'bitbucket-pipelines.yml',
    note: 'Same CLI again. Plan in one step, gate in the next.',
    url: 'https://bitbucket.org/__refeed__/tirith-bitbucket-demo',
    linkLabel: 'Open the Bitbucket demo',
    code: `- step:
    name: Terraform plan
    script:
      - terraform plan -out=tfplan -input=false
      - terraform show -json tfplan > plan.json
    artifacts: [plan.json]

- step:
    name: Policy gate
    script:
      - pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
      # - tirith lint .tirith/policies   # in dev, not in 1.2.0
      - tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error`,
  },
  {
    id: 'anyci',
    name: 'Any CI',
    file: 'Jenkins, Azure DevOps, CircleCI, a cron job',
    note:
      'Three commands on anything that can produce a plan. Jenkins gets a worked ' +
      'declarative pipeline in the docs, including how to keep exit 3 and exit 1 apart.',
    to: '/docs/tirith-usage/ci-integration/',
    linkLabel: 'Jenkins and other runners',
    code: `pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
# tirith lint .tirith/policies   # in dev, not in 1.2.0
tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error`,
  },
  {
    id: 'local',
    name: 'Local',
    file: 'your terminal',
    note:
      'The same gate on your own machine, before anything is pushed. Nothing leaves it, ' +
      'and the exit code means exactly what it means in CI.',
    to: '/docs/tirith-usage/editor-and-local/',
    linkLabel: 'Run it as you write',
    code: `pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
terraform plan -out=tfplan
terraform show -json tfplan > plan.json
tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error`,
  },
];

export const DEMO_REPOS = [
  {
    id: 'github',
    name: 'GitHub Actions',
    file: '.github/workflows/plan.yml',
    note: 'The Action wraps the CLI and adds the pull-request comment and check run.',
    url: 'https://github.com/StackGuardian/tirith-action-demo',
    code: `permissions:
  contents: read
  pull-requests: write
  checks: write

steps:
  - run: terraform show -json tfplan > plan.json
  - uses: StackGuardian/tirith-iac-governance-action@v2
    with:
      fail-on-error: true`,
  },
  {
    id: 'gitlab',
    name: 'GitLab CI',
    file: '.gitlab-ci.yml',
    note: 'No wrapper — the CLI directly, consuming the plan as an artifact.',
    url: 'https://gitlab.com/stackguardian/tirith-component-demo',
    code: `tirith:
  stage: policy
  image: python:3.12
  needs: [terraform-plan]
  script:
    - pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
    # - tirith lint .tirith/policies   # in dev, not in 1.2.0
    - tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error`,
  },
  {
    id: 'bitbucket',
    name: 'Bitbucket Pipelines',
    file: 'bitbucket-pipelines.yml',
    note: 'Same CLI again. Plan in one step, gate in the next.',
    url: 'https://bitbucket.org/__refeed__/tirith-bitbucket-demo',
    code: `- step:
    name: Policy gate
    script:
      - pip install "git+https://github.com/StackGuardian/tirith.git@1.2.0"
      # - tirith lint .tirith/policies   # in dev, not in 1.2.0
      - tirith -policy-path .tirith/policies -input-path plan.json --fail-on-error`,
  },
];

/**
 * Everywhere else Tirith runs. No demo repository for these, so they link at the
 * documentation that covers them rather than pretending to a worked example.
 */
export const INTEGRATIONS = [
  {
    glyph: '⎇',
    title: 'pre-commit',
    // Needs .pre-commit-hooks.yaml, which is not in this repository, and `tirith lint`,
    // which is not in the released CLI.
    inDev: true,
    body: 'A tirith-lint hook that will run when a policy file changes. Offline, no plan needed, and it catches the mistakes that read as real violations.',
    to: '/docs/tirith-usage/editor-and-local/',
  },
  {
    glyph: '{}',
    title: 'Your editor',
    // Needs .vscode/tasks.json, which is not in this repository, and the same lint command.
    inDev: true,
    body: 'VS Code tasks that will lint and evaluate in one keystroke — the loop to use while an agent is drafting the policy for you.',
    to: '/docs/tirith-usage/editor-and-local/',
  },
];

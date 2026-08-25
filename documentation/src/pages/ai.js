import Link from '@docusaurus/Link';
import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

import {EVENTS, track, usePageView} from '../analytics';
import {
  Action,
  DataTable,
  Hero,
  PageShell,
  REPO,
  Section,
  Todo,
  TrackedCode,
  issueUrl,
  styles,
} from '../components/site';

/*
 * ---------------------------------------------------------------------------
 * AI
 *
 * Job: show that Tirith is usable from a coding agent without the page
 * becoming the "vague AI-first copy" the messaging brief rules out.
 *
 * The discipline that keeps it concrete: every claim on this page names a
 * specific tool, a specific file or a specific command, and the install links
 * are real. The Tirith MCP server is a local stdio process (`tirith mcp`), so
 * the Cursor and VS Code deeplinks below encode an actual working config
 * rather than pointing at a hosted endpoint that would need an account.
 *
 * The one thing that is NOT real yet is the StackGuardian MCP package name --
 * it is a config constant with a visible TODO, the same pattern as the HubSpot
 * form and the sign-up URL.
 * ---------------------------------------------------------------------------
 */

// A local stdio server: no endpoint, no account, nothing to host. That is what
// makes genuine one-click installation possible here.
const LOCAL_CONFIG = {command: 'tirith', args: ['mcp']};

// Generated from LOCAL_CONFIG -- Cursor takes base64 JSON, VS Code takes
// URL-encoded JSON. Precomputed rather than encoded at render time because
// btoa is browser-only and this page is server-rendered too.
const CURSOR_LINK =
  'cursor://anysphere.cursor-deeplink/mcp/install?name=tirith&config=eyJjb21tYW5kIjoidGlyaXRoIiwiYXJncyI6WyJtY3AiXX0=';
const VSCODE_LINK =
  'vscode:mcp/install?%7B%22name%22%3A%22tirith%22%2C%22command%22%3A%22tirith%22%2C%22args%22%3A%5B%22mcp%22%5D%7D';

/*
 * The StackGuardian MCP server: a local package over stdio, reading the same
 * SG_API_TOKEN and SG_ORG that platform mode already uses. The package name is
 * not published here because it has not been supplied -- set it and the whole
 * section below turns into working install instructions.
 */
const SG_MCP_PACKAGE = null;

const TOOLS = [
  [
    'evaluate',
    'Run a policy against a document and return the real verdict (passed, failed or unevaluated) with the exit code a pipeline would see.',
    'The one that stops the guessing. A policy that matches nothing looks identical to one that works until it is run.',
  ],
  [
    'lint_policy',
    'Check a policy’s shape before it runs: unknown condition types, missing eval_expression, evaluators the expression never references.',
    'An unknown condition type reaches the engine as an ordinary failed check, so it reads as a real violation. Catching it here saves debugging infrastructure that is fine.',
  ],
  [
    'describe_provider',
    'List the providers, the operation_type values each accepts, and every condition type, read from the engine’s own registries.',
    'Agents invent plausible vocabulary. There is no IsPresent, no Exists, no Matches. This is the closed list.',
  ],
  [
    'explain_result',
    'Turn a result document into which rule failed, on which resource, and why.',
    'Point it at the JSON from a red CI job. It also says when a failure carries no resource address, rather than leaving you to wonder.',
  ],
];

const SKILL_FILES = [
  [
    '.claude/skills/tirith-policies/SKILL.md',
    'Claude Code, Claude Desktop',
    'The policy-authoring skill: schema, the closed condition list, provider operations, how to read a verdict, and the instruction to evaluate before claiming a policy works. Self-contained, so it can be copied into any repository.',
  ],
  [
    'AGENTS.md',
    'Codex, Cursor, Zed, and anything else that reads the convention',
    'For an agent working on Tirith itself: layout, how to run the suite, and the contracts that will bite: exit codes, the golden-file output test, optional extras that must degrade rather than crash.',
  ],
  [
    '.cursor/rules/tirith-policies.mdc',
    'Cursor',
    'The same vocabulary as the skill, scoped with globs so it attaches automatically when a file under .tirith/policies is open.',
  ],
];

export default function Ai() {
  usePageView(EVENTS.aiView);

  return (
    <PageShell
      title="Tirith with a coding agent: MCP server and skill files"
      description="Give a coding agent the real Tirith schema and a real verdict: an MCP server that evaluates, lints and explains policies, plus skill files for Claude, Cursor, Codex and VS Code."
    >
      <Hero
        eyebrow="Tirith with a coding agent"
        title="Let an agent draft the policy. Make the engine decide whether it works."
        body="Ask any agent to add a guardrail and it will write plausible JSON against a schema it is guessing at. Tirith ships an MCP server and skill files that replace the guessing with the real condition registry, the real provider operations, and a real verdict from the real engine, locally and with no account."
        trust={['Apache-2.0', 'Runs on your machine', 'No account', 'Any MCP client']}
        actions={[
          {label: 'Install it', href: '#install', primary: true, onClick: track(EVENTS.mcpInstall, {target: 'hero'})},
          {label: 'Read the skill file', href: `${REPO}/blob/main/.claude/skills/tirith-policies/SKILL.md`},
        ]}
      />

      <Section id="why" heading="What goes wrong without it">
        <p>
          Ask an agent for “a policy requiring an Owner tag on every resource” and you will
          usually get something like <code>{'"condition": {"type": "Exists"}'}</code>. It reads
          correctly. It is not a condition type Tirith has.
        </p>
        <p>
          The expensive part is what happens next. An unknown condition type does not raise an
          error. The engine returns it as an ordinary failed check with no error attached, so it
          is indistinguishable from a genuine violation. The build goes red, and somebody spends
          an afternoon looking at infrastructure that was fine all along.
        </p>
        <p className={styles.pullQuote}>
          The fix is not a better prompt. It is giving the agent the closed list, and making it
          run the policy before it claims the policy works.
        </p>
      </Section>

      <Section id="tools" heading="Four tools, one local process">
        <p>
          <code>tirith mcp</code> speaks the Model Context Protocol over stdio. Your editor starts
          it; it makes no network calls and writes nothing to disk, so pointing an agent at it
          cannot change anyone’s infrastructure.
        </p>

        <div className={styles.cards}>
          {TOOLS.map(([name, what, why]) => (
            <div key={name} className={styles.card}>
              <h3>
                <code>{name}</code>
              </h3>
              <p>{what}</p>
              <p className={styles.muted} style={{marginTop: '0.5rem'}}>
                {why}
              </p>
            </div>
          ))}
        </div>
      </Section>

      <Section id="install" heading="Install it">
        <p>
          The server ships as an optional extra, on the same terms as the interactive interface:
          a CI gate should not pay install time for a server it never starts.
        </p>

        <TrackedCode language="bash" ciSystem="cli">
          {"pip install 'py-tirith[mcp] @ git+https://github.com/StackGuardian/tirith.git'"}
        </TrackedCode>
        <p className={styles.muted}>
          Needs Python 3.10 or newer; Tirith itself supports 3.8, which is why this is an extra
          rather than a dependency.
        </p>

        <Tabs groupId="agent-client" queryString>
          <TabItem value="claude-code" label="Claude Code">
            <TrackedCode language="bash" ciSystem="cli">
              {'claude mcp add tirith -- tirith mcp'}
            </TrackedCode>
            <p className={styles.muted}>
              The skill file is picked up automatically from{' '}
              <code>.claude/skills/</code> when you work in a repository that has it. See{' '}
              <Link href="#skills">skill files</Link> below.
            </p>
          </TabItem>

          <TabItem value="cursor" label="Cursor">
            <p>
              <Action
                label="Add to Cursor"
                href={CURSOR_LINK}
                primary
                onClick={track(EVENTS.mcpInstall, {target: 'cursor'})}
              />
            </p>
            <p className={styles.muted}>
              One click, because the link carries the whole configuration. Cursor also reads{' '}
              <code>.cursor/rules/tirith-policies.mdc</code> automatically when a policy file is
              open.
            </p>
          </TabItem>

          <TabItem value="vscode" label="VS Code">
            <p>
              <Action
                label="Add to VS Code"
                href={VSCODE_LINK}
                primary
                onClick={track(EVENTS.mcpInstall, {target: 'vscode'})}
              />
            </p>
            <p className={styles.muted}>
              Opens VS Code’s MCP install prompt with the server pre-filled. On Insiders, swap the
              scheme for <code>vscode-insiders:</code>.
            </p>
          </TabItem>

          <TabItem value="claude-desktop" label="Claude Desktop">
            <p className={styles.muted}>
              Add to <code>claude_desktop_config.json</code>:
            </p>
            <TrackedCode language="json" ciSystem="none">
              {JSON.stringify({mcpServers: {tirith: LOCAL_CONFIG}}, null, 2)}
            </TrackedCode>
          </TabItem>

          <TabItem value="codex" label="Codex CLI">
            <p className={styles.muted}>
              Add to <code>~/.codex/config.toml</code>:
            </p>
            <TrackedCode language="toml" ciSystem="none">
              {'[mcp_servers.tirith]\ncommand = "tirith"\nargs = ["mcp"]'}
            </TrackedCode>
          </TabItem>

          <TabItem value="other" label="Anything else">
            <p className={styles.muted}>
              Any MCP client takes a command and arguments. There is no endpoint and no token:
            </p>
            <TrackedCode language="json" ciSystem="none">
              {JSON.stringify(LOCAL_CONFIG, null, 2)}
            </TrackedCode>
          </TabItem>
        </Tabs>
      </Section>

      <Section id="skills" heading="Skill files, if you would rather not run a server">
        <p>
          The MCP server is the better experience because the agent can evaluate a
          policy. But most of the value is knowing the vocabulary, and that is just a file: no
          install, no extra, no Python version floor. All three live in this repository and can be
          copied into yours.
        </p>

        <DataTable
          columns={['File', 'Read by', 'What it carries']}
          rows={SKILL_FILES.map(([path, client, what]) => [
            <Link key={path} href={`${REPO}/blob/main/${path}`} onClick={track(EVENTS.skillCopy, {file: path})}>
              <code>{path}</code>
            </Link>,
            client,
            what,
          ])}
        />

        <TrackedCode language="bash" ciSystem="cli">
          {'# Copy the policy-authoring skill into your own repository\n' +
            'mkdir -p .claude/skills\n' +
            'curl -sL https://raw.githubusercontent.com/StackGuardian/tirith/main/.claude/skills/tirith-policies/SKILL.md \\\n' +
            '  -o .claude/skills/tirith-policies/SKILL.md'}
        </TrackedCode>
      </Section>

      <Section id="scale" heading="Across every repository, not just the one you have open" tone="quiet">
        <p>
          An agent with the Tirith server can write and prove a policy in the repository in front
          of it. What it cannot do is tell you which of your two hundred repositories have no gate
          at all, which teams pinned four different provider versions, or which pipeline applies
          without a reviewed plan, because none of that is in the repository it is looking at.
        </p>
        <p>
          The StackGuardian MCP server puts that estate-wide view in the same conversation: ask
          which repositories are ungoverned, ask what a finding means, and open the installation
          pull requests from where you already are.
        </p>

        {SG_MCP_PACKAGE ? (
          <TrackedCode language="bash" ciSystem="cli">
            {`claude mcp add stackguardian -- npx -y ${SG_MCP_PACKAGE}`}
          </TrackedCode>
        ) : (
          <Todo>
            The StackGuardian MCP server is a local package over stdio, authenticated with the same{' '}
            <code>SG_API_TOKEN</code> and <code>SG_ORG</code> that platform mode already uses, but
            the package name has not been supplied, so no install command is shown and no
            one-click link is generated. Set <code>SG_MCP_PACKAGE</code> in this file and the
            command, the Cursor deeplink and the VS Code deeplink all follow from it. Until then
            this section describes something a reader cannot install.
          </Todo>
        )}

        <div className={styles.actions}>
          <Action
            label="See what fleet governance covers"
            to="/fleet"
            primary
            onClick={track(EVENTS.sgMcpInterest, {stage: 'ai-page'})}
          />
          <Action label="Keep it local instead" to="/docs/tirith-usage/ci-integration/" />
        </div>
      </Section>

      <Section id="boundaries" heading="What none of this does">
        <p>
          Worth being explicit, because “AI” on a governance page usually means something vaguer
          than this.
        </p>
        <ul>
          <li>
            <strong>Nothing here remediates your infrastructure.</strong> The tools read documents
            and return verdicts. An agent may propose a code change; a human reviews and merges it,
            as before.
          </li>
          <li>
            <strong>A drafted policy is a draft.</strong> Generated JSON is worth no more than the
            evaluation that follows it, which is why <code>evaluate</code> exists and why the
            skill file says never to hand back a policy you have not run against a document that
            should fail it.
          </li>
          <li>
            <strong>The engine is the arbiter, not the model.</strong> Every verdict on this site,
            and every verdict these tools return, comes from the same evaluator your pipeline runs.
          </li>
          <li>
            <strong>Nothing leaves your machine.</strong> The Tirith server makes no network call.
            Your agent may be a hosted model, which is between you and your agent, but the
            evaluation is local.
          </li>
        </ul>
      </Section>

      <Section id="next" heading="Try it on a policy that fails" tone="finale">
        <p>
          The quickest way to see whether this is worth installing: open the Playground, take a
          policy that catches a violation, and ask your agent to explain the verdict. If it can do
          that from the result document alone, you do not need the server. If it cannot, that is
          what <code>explain_result</code> is for.
        </p>
        <div className={styles.actions}>
          <Action label="Open the Playground" to="/playground" primary />
          <Action label="Browse the policies" to="/policies" />
        </div>
        <ul className={styles.inlineLinks}>
          <li>
            <Link href={issueUrl({template: 'general-issue.md', title: 'MCP: '})}>
              Report an issue with the server
            </Link>
          </li>
          <li>
            <Link href={`${REPO}/blob/main/AGENTS.md`}>Working on Tirith itself</Link>
          </li>
        </ul>
      </Section>
    </PageShell>
  );
}

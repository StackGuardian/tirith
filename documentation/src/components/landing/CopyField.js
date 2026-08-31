import {useCallback, useEffect, useRef, useState} from 'react';
import styles from '../../pages/index.module.css';

/**
 * The page's primary conversion action: a command that ends up on the clipboard.
 *
 * Deliberately not a <CodeBlock>. Docusaurus's copy button is a hover-revealed icon in
 * the corner of a code block -- correct for documentation, wrong for the one action the
 * landing page exists to drive, which has to read as a button before anyone hovers.
 *
 * The command stays selectable text so keyboard and screen-reader users can take it the
 * ordinary way when the clipboard API is unavailable or blocked.
 */
export default function CopyField({
  command,
  label,
  tone = 'primary',
  prompt = true,
  /*
   * Optional. Fired after the command reaches the clipboard, including via the
   * selection fallback below -- the user got the command either way, and a copy that
   * only counts on the happy path under-reports exactly the browsers where copying is
   * hardest. Left undefined by every call site that does not care.
   */
  onCopy,
}) {
  const [copied, setCopied] = useState(false);
  const timer = useRef(null);

  useEffect(() => () => clearTimeout(timer.current), []);

  const copy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(command);
    } catch {
      // Older browsers, and any context where the clipboard is denied. Falling back to
      // a selection means the user can still finish the job with one keystroke.
      const sel = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(document.getElementById(`cmd-${label}`));
      sel.removeAllRanges();
      sel.addRange(range);
    }
    onCopy?.();
    setCopied(true);
    clearTimeout(timer.current);
    timer.current = setTimeout(() => setCopied(false), 2000);
  }, [command, label, onCopy]);

  return (
    <div className={tone === 'primary' ? styles.copyField : styles.copyFieldQuiet}>
      <code id={`cmd-${label}`} className={styles.copyCommand}>
        {prompt ? <span className={styles.copyPrompt}>$</span> : null}
        {command}
      </code>
      <button
        type="button"
        className={styles.copyButton}
        onClick={copy}
        aria-label={`Copy: ${command}`}>
        <span aria-hidden="true">{copied ? 'COPIED' : 'COPY'}</span>
        <span className={styles.srOnly} role="status">
          {copied ? 'Copied to clipboard' : ''}
        </span>
      </button>
    </div>
  );
}

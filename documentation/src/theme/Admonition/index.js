import React from 'react';
import Admonition from '@theme-original/Admonition';
import InfoIcon from '@site/static/img/info.svg';
import DangerIcon from '@site/static/img/danger.svg';
import WarningIcon from '@site/static/img/warning.svg';
import TipIcon from '@site/static/img/tip.svg';

export default function AdmonitionWrapper(props) {
  if (props.type == 'info') {
    return <Admonition icon={<InfoIcon />} className="alert_info" {...props} />
  }
  if (props.type == 'danger') {
    return <Admonition icon={<DangerIcon />} className="alert_danger" {...props} />
  }
  if (props.type == 'warning') {
    return <Admonition icon={<WarningIcon />} className="alert_warning" {...props} />
  }
  if (props.type == 'tip') {
    return <Admonition icon={<TipIcon />} className="alert_tip" {...props} />
  }
  if (props.type == 'note') {
    return <Admonition className="alert_note"  {...props} />
  }
}
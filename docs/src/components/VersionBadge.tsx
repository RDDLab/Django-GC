import type {ReactNode} from 'react';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';

type Kind = 'since' | 'changed' | 'deprecated';

const labels: Record<'en' | 'ru', Record<Kind, string>> = {
  en: {
    since: 'Added in',
    changed: 'Changed in',
    deprecated: 'Deprecated in',
  },
  ru: {
    since: 'Добавлено в',
    changed: 'Изменено в',
    deprecated: 'Устарело в',
  },
};

function VersionBadge({v, kind}: {v: string; kind: Kind}): ReactNode {
  const {i18n} = useDocusaurusContext();
  const locale = i18n.currentLocale === 'ru' ? 'ru' : 'en';
  const className =
    kind === 'since'
      ? 'version-badge'
      : `version-badge version-badge--${kind}`;

  return (
    <span className={className}>
      {labels[locale][kind]} {v}
    </span>
  );
}

export function Since({v}: {v: string}): ReactNode {
  return <VersionBadge v={v} kind="since" />;
}

export function Changed({v}: {v: string}): ReactNode {
  return <VersionBadge v={v} kind="changed" />;
}

export function Deprecated({v}: {v: string}): ReactNode {
  return <VersionBadge v={v} kind="deprecated" />;
}

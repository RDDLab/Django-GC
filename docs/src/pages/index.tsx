import {useState, type ReactNode} from 'react';
import Link from '@docusaurus/Link';
import useBaseUrl from '@docusaurus/useBaseUrl';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

const PACKAGE_VERSION = '1.1.4';

type Copy = {
  title: string;
  description: string;
  kicker: string;
  heroTitle: {text: string; highlight?: boolean}[];
  lead: string;
  getStarted: string;
  api: string;
  github: string;
  install: string;
  copyInstall: string;
  copiedInstall: string;
  howTitle: string;
  steps: {title: string; body: string}[];
  featuresTitle: string;
  features: {title: string; body: string}[];
  guidesTitle: string;
  guides: {title: string; body: string; to: string}[];
};

const en: Copy = {
  title: 'Django-GC',
  description: 'Typed Django runtime configuration stored in the database and served from cache',
  kicker: 'Typed Django runtime configuration',
  heroTitle: [
    {text: 'Typed '},
    {text: 'runtime', highlight: true},
    {text: ' config for '},
    {text: 'Django', highlight: true},
  ],
  lead: 'Declare keys in code, store values in the database, and read them only through get_value(). The project owns the keys; this package is the mechanism.',
  getStarted: 'Get started',
  api: 'API reference',
  github: 'GitHub',
  install: 'pip install django-gc',
  copyInstall: 'Copy',
  copiedInstall: 'Copied',
  howTitle: 'From install to a working snapshot',
  steps: [
    {
      title: 'Install the package',
      body: 'Add django_gc, then declare categories and keys in settings.',
    },
    {
      title: 'Migrate',
      body: 'post_migrate creates missing rows and never overwrites live values.',
    },
    {
      title: 'Read through the service',
      body: 'Call get_value(). A cache miss rebuilds the full typed snapshot under a lock.',
    },
  ],
  featuresTitle: 'Why Django-GC',
  features: [
    {
      title: 'Code-declared keys',
      body: 'Categories and definitions live in Django settings and are synchronized after migrate.',
    },
    {
      title: 'Full cache snapshot',
      body: 'get_value() never falls back to a single-row ORM read. One parse failure aborts publish.',
    },
    {
      title: 'Stock Django Admin',
      body: 'Edit values with standard ModelAdmin and Django LogEntry history. No Tabler dependency.',
    },
    {
      title: 'Strongly typed',
      body: 'The package ships py.typed so editors and type checkers can follow the public contracts.',
    },
  ],
  guidesTitle: 'Guides',
  guides: [
    {title: 'How it works', body: 'Snapshot, lock, parse, and the read path.', to: '/docs/how-it-works'},
    {title: 'Definitions', body: 'CategoryDefinition, SettingDefinition, and post_migrate.', to: '/docs/definitions'},
    {title: 'Types', body: 'Every SettingType and its stored format.', to: '/docs/types'},
    {title: 'Admin', body: 'Stock ModelAdmin, read-only keys, and forms.', to: '/docs/admin'},
    {title: 'History', body: 'Django Admin LogEntry history.', to: '/docs/history'},
    {title: 'Cache', body: 'Django cache keys, readiness, and lock.', to: '/docs/cache'},
    {title: 'Settings', body: 'Settings, encryption key, and optional Celery.', to: '/docs/settings-and-checks'},
  ],
};

const ru: Copy = {
  title: 'Django-GC',
  description: 'Типизированные runtime-настройки Django в базе и в кэше',
  kicker: 'Типизированные runtime-настройки Django',
  heroTitle: [
    {text: 'Типизированный '},
    {text: 'runtime', highlight: true},
    {text: ' config для '},
    {text: 'Django', highlight: true},
  ],
  lead: 'Ключи объявляются в коде, значения хранятся в базе и читаются только через get_value(). Проект владеет ключами; этот пакет — механизм.',
  getStarted: 'Начало работы',
  api: 'Справочник API',
  github: 'GitHub',
  install: 'pip install django-gc',
  copyInstall: 'Копировать',
  copiedInstall: 'Скопировано',
  howTitle: 'От установки до рабочего снимка',
  steps: [
    {
      title: 'Установите пакет',
      body: 'Добавьте django_gc, затем объявите категории и ключи в settings.',
    },
    {
      title: 'Выполните migrate',
      body: 'post_migrate создаёт отсутствующие строки и не перезаписывает рабочие значения.',
    },
    {
      title: 'Читайте через сервис',
      body: 'Вызывайте get_value(). Cache miss пересобирает полный типизированный снимок под lock.',
    },
  ],
  featuresTitle: 'Почему Django-GC',
  features: [
    {
      title: 'Ключи из кода',
      body: 'Категории и definitions живут в Django settings и синхронизируются после migrate.',
    },
    {
      title: 'Полный снимок кэша',
      body: 'get_value() не читает одну строку из ORM. Ошибка разбора одного значения отменяет публикацию.',
    },
    {
      title: 'Стандартный Django Admin',
      body: 'Правка значений через обычный ModelAdmin и историю Django LogEntry. Без Tabler.',
    },
    {
      title: 'Строгая типизация',
      body: 'Пакет поставляет py.typed, чтобы редакторы и type checker видели публичные контракты.',
    },
  ],
  guidesTitle: 'Руководства',
  guides: [
    {title: 'Как это работает', body: 'Снимок, lock, разбор и путь чтения.', to: '/docs/how-it-works'},
    {title: 'Definitions', body: 'CategoryDefinition, SettingDefinition и post_migrate.', to: '/docs/definitions'},
    {title: 'Типы', body: 'Каждый SettingType и его формат хранения.', to: '/docs/types'},
    {title: 'Admin', body: 'Стандартный ModelAdmin, read-only ключи и формы.', to: '/docs/admin'},
    {title: 'История', body: 'История Django Admin через LogEntry.', to: '/docs/history'},
    {title: 'Кэш', body: 'Ключи Django cache, readiness и lock.', to: '/docs/cache'},
    {title: 'Настройки', body: 'Settings, ключ шифрования и необязательный Celery.', to: '/docs/settings-and-checks'},
  ],
};

function InstallCommand({
  command,
  copyLabel,
  copiedLabel,
}: {
  command: string;
  copyLabel: string;
  copiedLabel: string;
}): ReactNode {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(command);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return (
    <div className={styles.install}>
      <code>{command}</code>
      <button type="button" className={styles.installCopy} onClick={copy} aria-label={copyLabel}>
        {copied ? copiedLabel : copyLabel}
      </button>
    </div>
  );
}

export default function Home(): ReactNode {
  const {i18n} = useDocusaurusContext();
  const copy = i18n.currentLocale === 'ru' ? ru : en;
  const logoSrc = useBaseUrl('/img/icon.svg');

  return (
    <Layout title={copy.title} description={copy.description}>
      <header className={styles.hero}>
        <div className="container">
          <div className={styles.heroRow}>
            <div className={styles.heroCopy}>
              <p className={styles.kicker}>
                {copy.kicker}
                <span className={styles.version}>{`v${PACKAGE_VERSION}`}</span>
              </p>
              <Heading as="h1" className={styles.heroTitle}>
                {copy.heroTitle.map((part) =>
                  part.highlight ? (
                    <span className={styles.gradient} key={part.text}>
                      {part.text}
                    </span>
                  ) : (
                    <span key={part.text}>{part.text}</span>
                  ),
                )}
              </Heading>
              <p className={styles.heroLead}>{copy.lead}</p>
              <div className={styles.actions}>
                <Link className="button button--primary button--lg" to="/docs/getting-started">
                  {copy.getStarted}
                </Link>
                <Link className="button button--secondary button--lg" to="/docs/api-reference">
                  {copy.api}
                </Link>
                <Link
                  className="button button--secondary button--lg"
                  to="https://github.com/RDDLab/Django-GC"
                >
                  {copy.github}
                </Link>
              </div>
              <InstallCommand
                command={copy.install}
                copyLabel={copy.copyInstall}
                copiedLabel={copy.copiedInstall}
              />
            </div>
            <div className={styles.heroVisual} aria-hidden="true">
              <img className={styles.heroMark} src={logoSrc} alt="" width={220} height={220} />
            </div>
          </div>
        </div>
      </header>

      <main>
        <section className={styles.section}>
          <div className="container">
            <Heading as="h2" className={styles.sectionTitle}>
              {copy.howTitle}
            </Heading>
            <div className={styles.grid3}>
              {copy.steps.map((step, index) => (
                <article className={styles.card} key={step.title}>
                  <span className={styles.step}>{String(index + 1).padStart(2, '0')}</span>
                  <Heading as="h3">{step.title}</Heading>
                  <p>{step.body}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className={styles.section}>
          <div className="container">
            <Heading as="h2" className={styles.sectionTitle}>
              {copy.featuresTitle}
            </Heading>
            <div className={styles.grid4}>
              {copy.features.map((feature) => (
                <article className={styles.card} key={feature.title}>
                  <Heading as="h3">{feature.title}</Heading>
                  <p>{feature.body}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className={styles.section}>
          <div className="container">
            <Heading as="h2" className={styles.sectionTitle}>
              {copy.guidesTitle}
            </Heading>
            <div className={styles.guides}>
              {copy.guides.map((guide) => (
                <Link className={styles.guide} key={guide.to} to={guide.to}>
                  <Heading as="h3">{guide.title}</Heading>
                  <p>{guide.body}</p>
                </Link>
              ))}
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}

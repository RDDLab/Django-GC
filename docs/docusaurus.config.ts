import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const config: Config = {
  title: 'Django-GC',
  tagline: 'Typed Django runtime configuration',
  favicon: 'img/favicon.svg',

  url: 'https://django-gc.rdd-lab.com',
  baseUrl: '/',
  trailingSlash: true,
  organizationName: 'RDDLab',
  projectName: 'Django-GC',

  headTags: [
    {
      tagName: 'link',
      attributes: {
        rel: 'icon',
        type: 'image/svg+xml',
        href: '/img/favicon.svg',
      },
    },
  ],

  onBrokenLinks: 'throw',
  onBrokenAnchors: 'throw',
  markdown: {
    mermaid: true,
    hooks: {
      onBrokenMarkdownLinks: 'throw',
    },
  },

  i18n: {
    defaultLocale: 'en',
    locales: ['en', 'ru'],
    localeConfigs: {
      en: {
        label: 'English',
        htmlLang: 'en-US',
        baseUrl: '/',
      },
      ru: {
        label: 'Русский',
        htmlLang: 'ru-RU',
        baseUrl: '/ru/',
      },
    },
  },

  clientModules: ['./src/clientModules/stripEnPrefix.ts'],

  presets: [
    [
      'classic',
      {
        docs: {
          path: 'content',
          sidebarPath: './sidebars.ts',
          editUrl: 'https://github.com/RDDLab/Django-GC/tree/main/docs/',
          editLocalizedFiles: true,
        },
        blog: false,
        theme: {
          customCss: './src/css/custom.css',
        },
        sitemap: {
          lastmod: 'date',
          changefreq: 'weekly',
          filename: 'sitemap.xml',
        },
      } satisfies Preset.Options,
    ],
  ],

  themes: [
    '@docusaurus/theme-mermaid',
    [
      '@easyops-cn/docusaurus-search-local',
      {
        hashed: true,
        language: ['en', 'ru'],
        indexDocs: true,
        indexBlog: false,
        indexPages: true,
        docsDir: 'content',
        docsRouteBasePath: '/docs',
        explicitSearchResultPath: true,
      },
    ],
  ],

  plugins: [
    function i18nDevProxy() {
      return {
        name: 'i18n-dev-proxy',
        configureWebpack(_config: unknown, isServer: boolean) {
          if (
            isServer ||
            process.env.NODE_ENV === 'production' ||
            process.env.DOCUSAURUS_CURRENT_LOCALE === 'ru'
          ) {
            return {};
          }
          return {
            mergeStrategy: {'devServer.proxy': 'replace'},
            devServer: {
              proxy: [
                {
                  context: ['/ru'],
                  target: 'http://127.0.0.1:3101',
                  changeOrigin: true,
                  ws: true,
                },
              ],
            },
          };
        },
      };
    },
  ],

  themeConfig: {
    image: 'img/icon.svg',
    colorMode: {
      defaultMode: 'dark',
      respectPrefersColorScheme: true,
    },
    mermaid: {
      theme: {light: 'neutral', dark: 'dark'},
    },
    navbar: {
      title: 'Django-GC',
      logo: {
        alt: 'Django-GC',
        src: 'img/icon.svg',
        srcDark: 'img/icon.svg',
      },
      hideOnScroll: false,
      items: [
        {
          to: '/docs/getting-started',
          label: 'Guide',
          position: 'left',
          activeBaseRegex:
            '/docs(?!/api-reference(?:/|$)|/contrib(?:/|$))(?:/|$)',
        },
        {
          to: '/docs/api-reference',
          label: 'API Reference',
          position: 'left',
          activeBaseRegex: '/docs/api-reference(?:/$)',
        },
        {
          to: '/docs/contrib',
          label: 'Contributing',
          position: 'left',
          activeBaseRegex: '/docs/contrib(?:/$)',
        },
        {
          type: 'localeDropdown',
          position: 'right',
        },
        {
          href: 'https://github.com/RDDLab/Django-GC',
          label: 'GitHub',
          position: 'right',
        },
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Guide',
          items: [
            {label: 'Getting Started', to: '/docs/getting-started'},
            {label: 'How it works', to: '/docs/how-it-works'},
            {label: 'Definitions', to: '/docs/definitions'},
            {label: 'Cache', to: '/docs/cache'},
          ],
        },
        {
          title: 'Reference',
          items: [
            {label: 'API Reference', to: '/docs/api-reference'},
            {label: 'Settings and checks', to: '/docs/settings-and-checks'},
            {label: 'Types', to: '/docs/types'},
            {label: 'Contributing', to: '/docs/contrib'},
          ],
        },
        {
          title: 'Project',
          items: [
            {label: 'GitHub', href: 'https://github.com/RDDLab/Django-GC'},
            {label: 'PyPI', href: 'https://pypi.org/project/django-gc/'},
            {
              label: 'Changelog',
              href: 'https://github.com/RDDLab/Django-GC/blob/main/CHANGELOG.md',
            },
          ],
        },
      ],
      copyright: `MIT Licensed | Copyright © ${new Date().getFullYear()}`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'json', 'toml'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;

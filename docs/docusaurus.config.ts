import {themes as prismThemes} from 'prism-react-renderer';
import type {Config} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';

const YANDEX_METRIKA_ID = 111872297;

function yandexMetrika() {
  return {
    name: 'yandex-metrika',
    injectHtmlTags() {
      return {
        headTags: [
          {
            tagName: 'script',
            attributes: {
              type: 'text/javascript',
            },
            innerHTML: `
    (function(m,e,t,r,i,k,a){
        m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};
        m[i].l=1*new Date();
        for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}
        k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)
    })(window, document,'script','https://mc.yandex.ru/metrika/tag.js?id=${YANDEX_METRIKA_ID}', 'ym');

    ym(${YANDEX_METRIKA_ID}, 'init', {ssr:true, webvisor:true, clickmap:true, ecommerce:"dataLayer", referrer: document.referrer, url: location.href, accurateTrackBounce:true, trackLinks:true});
`,
          },
        ],
        postBodyTags: [
          {
            tagName: 'noscript',
            innerHTML: `<div><img src="https://mc.yandex.ru/watch/${YANDEX_METRIKA_ID}" style="position:absolute; left:-9999px;" alt="" /></div>`,
          },
        ],
      };
    },
  };
}

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

  clientModules: [
    './src/clientModules/stripEnPrefix.ts',
    './src/client/yandex-metrika.ts',
  ],

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
    yandexMetrika,
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

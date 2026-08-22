import type {SidebarsConfig} from '@docusaurus/plugin-content-docs';

const sidebars: SidebarsConfig = {
  docs: [
    {
      type: 'category',
      label: 'Start',
      collapsed: false,
      items: ['intro', 'getting-started', 'how-it-works'],
    },
    {
      type: 'category',
      label: 'Guide',
      items: ['definitions', 'types', 'admin', 'history', 'cache'],
    },
    {
      type: 'category',
      label: 'Reference',
      items: ['settings-and-checks', 'api-reference', 'contrib'],
    },
  ],
};

export default sidebars;

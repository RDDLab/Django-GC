import MDXComponents from '@theme-original/MDXComponents';
import Mermaid from '@theme/Mermaid';
import {Changed, Deprecated, Since} from '@site/src/components/VersionBadge';

export default {
  ...MDXComponents,
  mermaid: Mermaid,
  Mermaid,
  Since,
  Changed,
  Deprecated,
};

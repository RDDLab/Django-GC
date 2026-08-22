import {type ReactNode} from 'react';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import {translate} from '@docusaurus/Translate';
import {mergeSearchStrings, useHistorySelector} from '@docusaurus/theme-common';
import {useLocation} from '@docusaurus/router';
import DropdownNavbarItem from '@theme/NavbarItem/DropdownNavbarItem';
import IconLanguage from '@theme/Icon/Language';
import type {LinkLikeNavbarItemProps} from '@theme/NavbarItem';
import type {Props} from '@theme/NavbarItem/LocaleDropdownNavbarItem';

import styles from './styles.module.css';

function stripLocalePrefix(pathname: string): string {
  const stripped = pathname.replace(/^\/(?:en|ru)(?=\/|$)/, '');
  if (stripped !== pathname) {
    return stripLocalePrefix(stripped);
  }
  return stripped || '/';
}

function localePath(locale: string, pathname: string): string {
  const suffix = stripLocalePrefix(pathname);
  if (locale === 'en') {
    return suffix;
  }
  return suffix === '/' ? '/ru/' : `/ru${suffix}`;
}

export default function LocaleDropdownNavbarItem({
  mobile,
  dropdownItemsBefore,
  dropdownItemsAfter,
  queryString,
  ...props
}: Props): ReactNode {
  const {pathname} = useLocation();
  const search = useHistorySelector((history) => history.location.search);
  const hash = useHistorySelector((history) => history.location.hash);
  const {
    i18n: {currentLocale, locales, localeConfigs},
  } = useDocusaurusContext();

  const localeItems = locales.map((locale): LinkLikeNavbarItemProps => {
    const path = localePath(locale, pathname);
    const finalSearch = mergeSearchStrings([search, queryString], 'append');
    return {
      label: localeConfigs[locale]?.label ?? locale,
      lang: localeConfigs[locale]?.htmlLang,
      href: `pathname://${path}${finalSearch}${hash}`,
      target: '_self',
      prependBaseUrlToHref: false,
      autoAddBaseUrl: false,
      className:
        locale === currentLocale
          ? mobile
            ? 'menu__link--active'
            : 'dropdown__link--active'
          : '',
    };
  });

  const items = [...dropdownItemsBefore, ...localeItems, ...dropdownItemsAfter];
  const dropdownLabel = mobile
    ? translate({
        message: 'Languages',
        id: 'theme.navbar.mobileLanguageDropdown.label',
        description: 'The label for the mobile language switcher dropdown',
      })
    : (localeConfigs[currentLocale]?.label ?? currentLocale);

  return (
    <DropdownNavbarItem
      {...props}
      mobile={mobile}
      label={
        <>
          <IconLanguage className={styles.iconLanguage} />
          {dropdownLabel}
        </>
      }
      items={items}
    />
  );
}

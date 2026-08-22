/**
 * Default locale is `/`, not `/en/`. Send leftover `/en/` links there.
 */
if (typeof window !== 'undefined') {
  const {pathname, search, hash} = window.location;
  if (pathname === '/en' || pathname.startsWith('/en/')) {
    const rest = pathname.slice('/en'.length);
    window.location.replace(`${rest || '/'}${search}${hash}`);
  }
}

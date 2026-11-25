#!/usr/bin/env bash
set -euo pipefail

find django_gc/locale -name '*.po' -type f -exec bash -ec '
    for catalog do
        msgfmt --check -o "${catalog%.po}.mo" "$catalog"
    done
' bash {} +

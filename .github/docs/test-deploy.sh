#!/bin/bash
set -euo pipefail

docs_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
sha=0123456789abcdef0123456789abcdef01234567
expected='Expected a full commit SHA and a host port from 1 to 65535.'
reject_deploy_arguments() {
    local output
    if output=$(bash "$docs_dir/deploy-docs.sh" "$@" 2>&1) || [[ "$output" != "$expected" ]]; then
        echo 'The deployment script accepted invalid arguments.' >&2
        exit 1
    fi
}
reject_deploy_arguments "$sha"
reject_deploy_arguments bad-sha 18080
reject_deploy_arguments "$sha" 0
reject_deploy_arguments "$sha" 65536
reject_deploy_arguments "$sha" 18080 extra

if command -v flock >/dev/null; then
    test_home=$(mktemp -d)
    trap 'rm -rf -- "$test_home"' EXIT
    HOME="$test_home" bash "$docs_dir/prepare-server.sh" "$sha"
    HOME="$test_home" bash "$docs_dir/prepare-server.sh" "$sha"
    prepared="$test_home/.local/share/django-gc-docs/$sha"
    cmp -s "$docs_dir/deploy-docs.sh" "$prepared/deploy-docs.sh"
    cmp -s "$docs_dir/compose.yml" "$prepared/compose.yml"
fi

export DOCS_IMAGE=django-gc-docs:test
compose_config() {
    docker compose --env-file /dev/null --file "$docs_dir/compose.yml" config --format json
}

for port in 18080 28080; do
    DOCS_PORT="$port" compose_config | jq -e --arg port "$port" '
        .services.docs.ports | length == 1 and
        .[0].host_ip == "127.0.0.1" and .[0].published == $port and .[0].target == 8080
    ' >/dev/null
done

if DOCS_PORT='' compose_config >/dev/null 2>&1; then
    echo 'Compose accepted a missing documentation host port.' >&2
    exit 1
fi

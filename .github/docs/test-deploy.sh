#!/bin/bash
set -euo pipefail

docs_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
sha=0123456789abcdef0123456789abcdef01234567
workflow_run=100-1
expected='Expected a full commit SHA, a host port from 1 to 65535, and a workflow run and attempt.'
reject_deploy_arguments() {
    local output
    if output=$(bash "$docs_dir/deploy-docs.sh" "$@" 2>&1) || [[ "$output" != "$expected" ]]; then
        echo 'The deployment script accepted invalid arguments.' >&2
        exit 1
    fi
}
reject_deploy_arguments "$sha" 18080
reject_deploy_arguments bad-sha 18080 "$workflow_run"
reject_deploy_arguments "$sha" 0 "$workflow_run"
reject_deploy_arguments "$sha" 65536 "$workflow_run"
reject_deploy_arguments "$sha" 18080 invalid-run
reject_deploy_arguments "$sha" 18080 "$workflow_run" extra

if command -v flock >/dev/null; then
    test_home=$(mktemp -d)
    trap 'rm -rf -- "$test_home"' EXIT
    mkdir "$test_home/bin"
    cat > "$test_home/bin/ssh" <<'SH'
#!/bin/bash
set -euo pipefail
exec bash -c "${@: -1}"
SH
    chmod +x "$test_home/bin/ssh"

    for _ in 1 2; do
        HOME="$test_home" PATH="$test_home/bin:$PATH" SSH_HOST=docs.example.invalid SSH_PORT=22 \
            SSH_USER=deploy SSH_PRIVATE_KEY=mock SSH_HOST_KEY='ssh-ed25519 AAAA' \
            bash "$docs_dir/prepare-over-ssh.sh" "$sha"
    done
    prepared="$test_home/.local/share/django-gc-docs/$sha"
    cmp -s "$docs_dir/deploy-docs.sh" "$prepared/deploy-docs.sh"
    cmp -s "$docs_dir/compose.yml" "$prepared/compose.yml"

    cat > "$test_home/bin/docker" <<'SH'
#!/bin/bash
set -euo pipefail

case "$1 $2" in
    'image load')
        [[ "$*" == 'image load --quiet' ]]
        [[ "$(gzip -dc)" == "$TEST_LOADED_RUN" ]]
        ;;
    'image inspect')
        printf '%s %s\n' "$TEST_DOCS_SHA" "$TEST_LOADED_RUN"
        ;;
    'image tag')
        [[ "$3" == previous-image && "$4" == *:rollback ]]
        ;;
    'compose --project-name')
        shift 7
        case "$*" in
            'ps --all --quiet docs')
                if [[ "$TEST_HEALTH" != healthy ]]; then
                    printf '%s\n' previous
                fi
                ;;
            'up --detach --no-build --wait --wait-timeout 60')
                if [[ "$DOCS_IMAGE" == *:rollback ]]; then
                    [[ "$DOCS_PORT" == 28080 ]]
                    touch "$HOME/container-restored"
                else
                    touch "$HOME/container-started"
                fi
                ;;
            'ps --quiet docs') printf '%s\n' docs ;;
            *) exit 1 ;;
        esac
        ;;
    'inspect --format')
        case "$3 $4" in
            '{{.Image}} previous') printf '%s\n' previous-image ;;
            *' previous') printf '%s\n' 28080 ;;
            *) printf '%s %s %s\n' "$TEST_DOCS_SHA" "$TEST_LOADED_RUN" "$TEST_HEALTH" ;;
        esac
        ;;
    *) exit 1 ;;
esac
SH
    chmod +x "$test_home/bin/docker"

    deploy_test_image() {
        printf '%s' "$1" | gzip -1 |
            HOME="$test_home" PATH="$test_home/bin:$PATH" DOCKER_CONTEXT=docs-test \
                TEST_DOCS_SHA="$sha" TEST_LOADED_RUN="$1" TEST_HEALTH="$2" \
                bash "$prepared/deploy-docs.sh" "$sha" 18080 "$workflow_run"
    }

    if deploy_test_image 100-2 healthy || [[ -e "$test_home/container-started" ]]; then
        echo 'An unexpected image reached the documentation service.' >&2
        exit 1
    fi
    deploy_test_image "$workflow_run" healthy
    test -e "$test_home/container-started"
    if deploy_test_image "$workflow_run" unhealthy; then
        echo 'The deployment accepted an unhealthy documentation container.' >&2
        exit 1
    fi
    test -e "$test_home/container-restored"
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

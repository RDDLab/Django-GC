#!/bin/bash
set -euo pipefail
umask 077

if (( $# != 2 )) || [[ ! "$1" =~ ^[0-9a-f]{40}$ || ! "$2" =~ ^[1-9][0-9]{0,4}$ ]] ||
   (( $2 > 65535 )); then
    echo 'Expected a full commit SHA and a host port from 1 to 65535.' >&2
    exit 1
fi
sha=$1
export DOCS_PORT=$2

state_dir="$HOME/.local/state/django-gc-docs"
deploy_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
compose_file="$deploy_dir/compose.yml"

# Use a rootless socket when SSH did not start a session and Docker has no custom context.
docker_socket="/run/user/$(id -u)/docker.sock"
if [[ -z "${DOCKER_HOST:-}" && -z "${DOCKER_CONTEXT:-}" && -S "$docker_socket" ]] &&
   [[ "$(docker context show)" == default ]]; then
    export DOCKER_HOST="unix://$docker_socket"
fi

mkdir -p "$state_dir"
exec 9>"$state_dir/deploy.lock"
flock -w 300 9

compose() {
    docker compose --project-name django-gc-docs --env-file /dev/null --file "$compose_file" "$@"
}

cleanup() {
    local status=$?
    trap - EXIT
    trap '' HUP INT TERM

    if [[ "$restore_service" == true ]]; then
        echo 'Deployment failed. Restoring the previous documentation service.' >&2
        if [[ -n "$previous_image" ]]; then
            export DOCS_IMAGE=django-gc-docs:rollback DOCS_PORT="$previous_port"
            if ! { docker image tag "$previous_image" "$DOCS_IMAGE" && compose up --detach --wait --wait-timeout 60; }; then
                echo 'Could not restore the previous documentation image.' >&2
            fi
        else
            compose down || echo 'Could not remove the failed documentation container.' >&2
        fi
    fi

    rm -rf -- "$release_dir"
    exit "$status"
}

release_dir=$(mktemp -d "$state_dir/release.XXXXXXXX")
restore_service=false
previous_image=''
previous_port=''
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

tar -xf - -C "$release_dir"
if [[ -f "$release_dir/.github/docs/Dockerfile" ]]; then
    build_context="$release_dir"
    dockerfile="$build_context/.github/docs/Dockerfile"
else
    build_context="$release_dir/docs"
    dockerfile="$build_context/Dockerfile"
fi
if [[ ! -f "$dockerfile" ]]; then
    echo 'The documentation archive does not contain a Dockerfile.' >&2
    exit 1
fi
export DOCS_IMAGE=django-gc-docs:"$sha"
previous_container=$(compose ps --all --quiet docs)
if [[ -n "$previous_container" ]]; then
    previous_image=$(docker inspect --format '{{.Image}}' "$previous_container")
    previous_port=$(docker inspect --format '{{range index .HostConfig.PortBindings "8080/tcp"}}{{.HostPort}}{{end}}' "$previous_container")
    if [[ ! "$previous_port" =~ ^[1-9][0-9]{0,4}$ ]] || (( previous_port > 65535 )); then
        echo 'Could not determine the previous documentation host port for rollback.' >&2
        exit 1
    fi
fi

docker build --file "$dockerfile" --tag "$DOCS_IMAGE" "$build_context"
new_image=$(docker image inspect --format '{{.Id}}' "$DOCS_IMAGE")
restore_service=true
compose up --detach --wait --wait-timeout 60
running_container=$(compose ps --quiet docs)
if [[ -z "$running_container" ]] ||
   [[ "$(docker inspect --format '{{.Image}} {{.State.Health.Status}}' "$running_container")" != "$new_image healthy" ]]; then
    echo 'The new documentation image did not become healthy.' >&2
    exit 1
fi
restore_service=false
echo "Deployed documentation from $sha."

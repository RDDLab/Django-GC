#!/bin/bash
set -euo pipefail
umask 077

ipv4_octet='(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])'
if (( $# != 4 )) || [[ ! "$1" =~ ^[0-9a-f]{40}$ || ! "$2" =~ ^[1-9][0-9]{0,4}$ ||
      ! "$3" =~ ^[0-9]+-[0-9]+$ || ! "$4" =~ ^($ipv4_octet\.){3}$ipv4_octet$ ]] || (( $2 > 65535 )); then
    echo 'Expected a full commit SHA, host port, workflow run and attempt, and IPv4 address.' >&2
    exit 1
fi
sha=$1
export DOCS_PORT=$2 DOCS_IP=$4
image_build="$sha $3"

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
echo 'Waiting for the documentation deployment lock.'
flock -w 300 9

compose() {
    local files=(--file "$compose_file")
    if [[ -n "$DOCS_IP" ]]; then
        files+=(--file "$deploy_dir/compose.network.yml")
    fi
    docker compose --project-name django-gc-docs --env-file /dev/null "${files[@]}" "$@"
}

cleanup() {
    local status=$?
    trap - EXIT
    trap '' HUP INT TERM

    if [[ "$restore_service" == true ]]; then
        echo 'Deployment failed. Restoring the previous documentation service.' >&2
        if [[ -n "$previous_image" ]]; then
            export DOCS_IMAGE=django-gc-docs:rollback DOCS_PORT="$previous_port" DOCS_IP="$previous_ip"
            if ! { docker image tag "$previous_image" "$DOCS_IMAGE" && compose up --detach --no-build --wait --wait-timeout 60; }; then
                echo 'Could not restore the previous documentation image.' >&2
            fi
        else
            compose down || echo 'Could not remove the failed documentation container.' >&2
        fi
    fi

    exit "$status"
}

restore_service=false
previous_image=''
previous_port=''
previous_ip=''
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

export DOCS_IMAGE=django-gc-docs:"$sha"
if ! docker network inspect docs_net >/dev/null; then
    echo 'The external Docker network docs_net must exist on the documentation server.' >&2
    exit 1
fi

previous_container=$(DOCS_IP="" compose ps --all --quiet docs)
if [[ -n "$previous_container" ]]; then
    previous_ip=$(docker inspect --format '{{with index .NetworkSettings.Networks "docs_net"}}{{if and .IPAMConfig .IPAMConfig.IPv4Address}}{{.IPAMConfig.IPv4Address}}{{else}}{{.IPAddress}}{{end}}{{end}}' "$previous_container")
    previous_image=$(docker inspect --format '{{.Image}}' "$previous_container")
    previous_port=$(docker inspect --format '{{range index .HostConfig.PortBindings "8080/tcp"}}{{.HostPort}}{{end}}' "$previous_container")
    if [[ ! "$previous_port" =~ ^[1-9][0-9]{0,4}$ ]] || (( previous_port > 65535 )); then
        echo 'Could not determine the previous documentation host port for rollback.' >&2
        exit 1
    fi
fi

echo 'Loading the documentation image built by GitHub Actions.'
docker image load --quiet
image_labels='{{index .Config.Labels "org.opencontainers.image.revision"}} {{index .Config.Labels "org.rddlab.docs.workflow-run"}}'
if [[ "$(docker image inspect --format "$image_labels" "$DOCS_IMAGE")" != "$image_build" ]]; then
    echo 'The loaded documentation image does not match the requested revision and workflow run.' >&2
    exit 1
fi

echo 'Starting the documentation container and checking readiness.'
restore_service=true
compose up --detach --no-build --wait --wait-timeout 60
running_container=$(compose ps --quiet docs)
if [[ -z "$running_container" ]] ||
   [[ "$(docker inspect --format "$image_labels {{.State.Health.Status}}" "$running_container")" != "$image_build healthy" ]]; then
    echo 'The new documentation image did not become healthy.' >&2
    exit 1
fi
restore_service=false
echo "Deployed documentation from $sha."

#!/bin/bash
set -euo pipefail
umask 077

if [[ ! "${SSH_ORIGINAL_COMMAND:-}" =~ ^([0-9a-f]{40})[[:blank:]]([1-9][0-9]{0,4})$ ]] ||
   (( BASH_REMATCH[2] > 65535 )); then
    echo 'Expected a full commit SHA and a host port from 1 to 65535 as the SSH command.' >&2
    exit 1
fi
sha=${BASH_REMATCH[1]}
export DOCS_PORT="${BASH_REMATCH[2]}"

state_dir="$HOME/.local/state/django-gc-docs"
repo="$state_dir/repository.git"
compose_file=/usr/local/share/django-gc-docs/compose.yml

# Use the dedicated rootless daemon even when SSH has no login session.
DOCKER_HOST="unix:///run/user/$(id -u)/docker.sock"
export DOCKER_HOST
unset DOCKER_CONTEXT

mkdir -p "$state_dir"
exec 9>"$state_dir/deploy.lock"
flock -w 300 9

if [[ ! -d "$repo/objects" ]]; then
    git init --bare "$repo"
fi
git --git-dir="$repo" fetch --no-tags https://github.com/RDDLab/Django-GlobalConfig.git \
    '+refs/heads/main:refs/heads/main'
if ! git --git-dir="$repo" merge-base --is-ancestor "$sha" refs/heads/main; then
    echo 'The documentation revision must be a commit in main.' >&2
    exit 1
fi

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

git --git-dir="$repo" archive "$sha" docs .github/docs | tar -x -C "$release_dir"
dockerfile="$release_dir/.github/docs/Dockerfile"
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

docker build --file "$dockerfile" --tag "$DOCS_IMAGE" "$release_dir"
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

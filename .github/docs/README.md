# Deploy the Django-GC documentation

Pushes to any branch and pull requests run security checks. On `main`, a single
push workflow runs security checks followed by testing. Other protected branches
start testing for the current branch head after a successful push scan. To deploy,
run **Documentation** on `main` or dispatch it from another workflow.
The release workflow dispatches it after PyPI accepts the package. It
passes the release commit, which must belong to `main`. A manual run
without a commit deploys the `main` revision selected at launch.

```sh
gh workflow run docs.yml --repo RDDLab/Django-GlobalConfig --ref main
```

To retry a specific revision, pass `-f source_sha=<full-commit-sha>`.
The server builds the Dockerfile from the selected revision. Both documentation
deployment and PyPI publishing require security and test checks for the exact
revision. The separate **Security checks** workflow runs Gitleaks, Python and
Django SAST and dependency checks, JavaScript and TypeScript SAST and npm
audit, then checks GitHub Actions. The verification job checks the result of
the existing `testing.yml` run on `main` for that SHA after scanning.
Publish the current head of `main` after its tests succeed. Check the
**Documentation** run for the deployment result.

### PyPI Trusted Publishing

Configure the PyPI trusted publisher for organization `RDDLab`, repository
`Django-GlobalConfig`, workflow file `publish.yml`, and GitHub Environment
`pypi`. Protect that environment with approved release tags and required
reviewers. Permit `main` if you use manual publishing from it.

### GitHub secrets and variables

In **Settings → Environments**, create `docs-production`. Under
**Deployment branches and tags**, choose **Selected branches and tags**
and add the branch `main`. Add these five **Environment secrets**.

| Secret | Value |
|---|---|
| `SSH_HOST` | The server hostname or IP, without a scheme or port |
| `SSH_PORT` | The SSH port, for example `22` |
| `SSH_PRIVATE_KEY` | The entire dedicated private key, with line breaks and both delimiters |
| `SSH_USER` | Account authorised to deploy the documentation |
| `SSH_HOST_KEY` | Server's ED25519 public host key |

Add `DOCS_PORT` as an **Environment variable**.

| Variable | Value |
|---|---|
| `DOCS_PORT` | Free loopback port for this documentation site, for example `18080` |

Assign each documentation site on the host its own `DOCS_PORT`.
Set `SSH_USER` to the existing deployment account, for example `deploy`. For `SSH_HOST_KEY`, use the first two
fields of the server's `/etc/ssh/ssh_host_ed25519_key.pub`, for example
`ssh-ed25519 AAAA…`. Obtain the key through the server console or its
administrator. From the server console, print the two fields with:

```sh
awk '{print $1, $2}' /etc/ssh/ssh_host_ed25519_key.pub
```

The workflow derives the host and port in `known_hosts`
from the two secrets.

Generate a dedicated ED25519 key without a passphrase for this unattended
job. Install its public half on the server. To upload the private half
without pasting it into a shell command, use GitHub CLI.

```sh
ssh-keygen -t ed25519 -f ./gc-docs-ci -C django-gc-docs-ci
gh secret set SSH_PRIVATE_KEY --env docs-production --repo RDDLab/Django-GlobalConfig < ./gc-docs-ci
```

### Server preparation and deployment

Use an existing unprivileged account that can execute commands over SSH and
access Docker with Compose V2. Bash, tar, and flock must be available on the host.
The existing GitHub Actions key can use the `restrict` option in
`~/.ssh/authorized_keys`. Use a key that can execute the workflow's SSH
commands. For a key previously configured with `command=`, use a dedicated
key without that option for both preparation and deployment.

After the checks succeed, the preparation job in `docs.yml` reads the
`docs-production` secrets directly. It sends the deployment script and
Compose file over SSH and installs both together under
`$HOME/.local/share/django-gc-docs/<workflow-sha>/`. Repeating the
preparation for the same revision reuses the installed files. To prepare
the server by itself, run **Prepare documentation server** from `main`.

The deploy job sends a source archive for the selected commit from its GitHub
checkout. The SSH account builds and updates the container with its Docker
context or socket. When a rootless socket is available and no custom Docker
context is selected, the script uses that socket. Both jobs run with the
existing account's permissions.

Point the HTTPS reverse proxy for `django-gc.rdd-lab.com` at
`127.0.0.1:<DOCS_PORT>`. Angie and the container health check use the
container's internal port `8080`.

The deployment lock serializes updates. The container checks both `/`
and `/ru/`. If the new deployment fails, the script restores the previous
image and host port and reports a failed run. To roll back a healthy
deployment, dispatch the workflow with a previously deployed commit.
The workflow uses the current `DOCS_PORT` for that deployment.

The server builds from a source archive. The sitemap uses Git dates when built from a full checkout.

### Container build

The Dockerfile has three stages. `dependencies` uses Node.js 24.22.3 LTS,
installs the npm version pinned in `docs/package.json`, and installs
dependencies from the lockfile. `site-build` copies the documentation
sources and builds both locales. `runtime` copies the generated files and
Angie configuration into the official Angie 1.12.5 minimal image.

Run the build from the repository root.

```sh
docker build --file .github/docs/Dockerfile --tag django-gc-docs:local .
```

Angie runs as the `angie` user with a read-only root filesystem under Compose.
It stores its PID and temporary files in the `/tmp` mount and writes
access and error logs to stdout and stderr.

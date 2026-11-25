# Deploy the Django-GC documentation

Pushes to `main` and pull requests targeting it run **Security checks**
and the test workflow. To deploy,
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
audit, then checks GitHub Actions. The shared CI then runs the Python checks
and matrix one job at a time, builds the wheel and sdist, and type-checks
and builds both documentation locales. A failing check stops publishing. Check
the **Documentation** run for the deployment result.

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
Set `SSH_USER` to `docs-deploy`. For `SSH_HOST_KEY`, use the first two
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

### Server setup

1. Create the unprivileged `docs-deploy` account with a home directory,
   a shell for OpenSSH's forced command, and its own rootless Docker
   daemon with Docker Compose V2. Enable the rootless Docker user service
   and lingering so the daemon remains available without a login session.
   Install Git, Bash, tar, and flock. Configure outbound access to GitHub,
   the npm registry, and the container registries. For a private Git
   repository, configure read-only Git HTTPS credentials for this account.
2. From a reviewed revision, install the deployment script and Compose
   file as root-owned files. The CI key can invoke only this installed
   script.

   ```sh
   sudo install -m 0755 .github/docs/deploy-docs.sh /usr/local/bin/django-gc-docs-deploy
   sudo install -d -m 0755 /usr/local/share/django-gc-docs
   sudo install -m 0644 .github/docs/compose.yml /usr/local/share/django-gc-docs/compose.yml
   ```

3. In the account's `.ssh/authorized_keys`, prepend
   `restrict,command="/usr/local/bin/django-gc-docs-deploy"` to the
   dedicated public key. Set `.ssh` to mode 0700 and `authorized_keys`
   to 0600, both owned by `docs-deploy`. The GitHub Actions runner must
   be able to reach the configured SSH port.
4. Point the existing HTTPS reverse proxy for
   `django-gc.rdd-lab.com` at `127.0.0.1:<DOCS_PORT>`. When you
   change this setting, update the proxy upstream to match.

Install both server files before the first deployment.
The workflow sends the commit SHA and host port to the forced SSH command.
The server validates both, fetches `main` from GitHub and checks that the
commit belongs to it. Rootless Docker builds and serves the site. Angie
and the container health check use its internal port `8080`.

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

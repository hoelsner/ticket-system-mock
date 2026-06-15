# n8n Node Use And Build

## Purpose

This guide gives contributors a project-level overview of how the n8n node
package is used and built in this repository.

Use it when you need to understand the role of the n8n package, build it
locally, stage it in the custom node directory layout, or verify how it is
delivered with the web application image.

## Table of Contents

- [Role in the project](#role-in-the-project)
- [Current node surface](#current-node-surface)
- [Repository location](#repository-location)
- [Local build commands](#local-build-commands)
- [Local n8n development instance](#local-n8n-development-instance)
- [Pack and stage the node](#pack-and-stage-the-node)
- [How the webapp image bundles the package](#how-the-webapp-image-bundles-the-package)
- [Recommended contributor workflow](#recommended-contributor-workflow)
- [Related documents](#related-documents)

## Role in the Project

The n8n package is a private **Integration System** for the project's
**REST API**.

Keep this boundary explicit:

- the **Web Application** remains the system of record
- the **REST API** remains the machine-facing contract
- the n8n package turns n8n workflow input into API calls and trigger behavior
- the n8n package must not depend on code outside `src/n8n_node`

When the REST API or webhook payload contract changes, treat the bundled n8n
package as part of the same shipped surface. Update the source nodes, rebuild
`dist/`, refresh the n8n tests, and keep the user-facing integration docs in
the same change set.

This separation matters because the package is designed to stay self-contained
for build, packaging, and installation.

## Current Node Surface

The package currently exposes these nodes:

| Node | Purpose |
| --- | --- |
| `TSM - Reference Data` | Read health, profile, group, and user data. |
| `TSM - Collection` | Read and mutate collection reference data. |
| `TSM - Category` | Read and mutate Issue category reference data. |
| `TSM - Issue` | List, fetch, create, update, archive, and move an **Issue**. |
| `TSM - Issue Attachment` | Add, update, and delete **Issue** attachments. |
| `TSM - Issue Activity` | Add or update an **Issue Comment** and preserve comment-plus-attachment compatibility flows. |
| `TSM - Issue Poll Trigger` | Poll the API for Issue changes. |
| `TSM - Issue Webhook Trigger` | Receive outbound webhook deliveries from the application. |

For operator-facing setup and usage, see the user guide instead of repeating it
in contributor docs.

## Repository Location

The package lives under:

```text
src/n8n_node/
```

Key files and directories:

- `package.json` defines the package metadata and the build scripts
- `credentials/` contains the shared API credential
- `nodes/` contains the node implementations and codex metadata
- `tools/copy-assets.js` copies node assets into the built output
- `build/` contains the packaged `.tgz` archive after `npm run pack:node`
- `dist/` contains the compiled JavaScript output after `npm run build`

## Local Build Commands

Run these commands from `src/n8n_node/` when working directly on the package:

```bash
npm install
npm run build
```

The repository devcontainer definitions already target Node `22` for Node-based
tooling. If an existing local devcontainer still reports Node `20`, rebuild the
container before treating that runtime as the repository baseline.

The package currently keeps an `isolated-vm` override in `package.json` so the
installed `n8n-workflow` line also works in local environments that stay on
Node `26`. Clean validation checks confirmed that Node `22` and Node `24` do
not need that override for this package, but Node `26` still does.

The `build` script runs TypeScript compilation and then copies the required
node assets into `dist/`.

Repository-level shortcuts are also available from the repository root:

```bash
make n8n-node-build
make n8n-node-lint
make n8n-node-audit
make n8n-node-stage-dev-package
make n8n-node-test
make n8n-node-test-coverage
make n8n-node-test-coverage-python-threshold
make n8n-node-pack
make n8n-node-validate-package
./scripts/build_n8n_for_devserver.bash
```

Use `make n8n-node-build` for the normal contributor build check. Use
`make n8n-node-lint` to run the package `typecheck` and ESLint rules, including
the initial cyclomatic complexity gate. Use
`make n8n-node-audit` to run `npm audit` with a high-severity threshold when you
want a dependency vulnerability check. Use
`make n8n-node-stage-dev-package` when you want to prepare the local Docker-based
n8n development instance with a package-shaped custom node directory. Use
`make n8n-node-test` to run the package unit tests against the built node
output.
Use
`make n8n-node-test-coverage` when you want the package coverage gate and saved
coverage summary under `src/n8n_node/covreport/`. Use
`make n8n-node-test-coverage-python-threshold` when you want to check the package
against the Python projects' current `98%` line-coverage bar. The default n8n
coverage gate now uses that same threshold, and this explicit alias remains
available when you want the comparison called out by name.
Use
`make n8n-node-test` for the fast unit-test loop and `make n8n-node-test-coverage`
before merging changes that affect shipped behavior.
Use
`make n8n-node-pack` when you need the installable tarball. Use
`make n8n-node-validate-package` when you want to verify that the packaged
archive was created and still contains the expected node and credential files.
Use
`./scripts/build_n8n_for_devserver.bash` when you want to pack the node and
stage the resulting archive in `build/integrations` for the local development
server.

When working directly inside `src/n8n_node/`, the package now also exposes a
basic local validation loop:

```bash
npm run typecheck
npm run audit
npm run lint
npm test
npm run test:coverage
npm run test:coverage:python-threshold
```

The coverage command checks the current built JavaScript output in `dist/`
because the package tests execute against the built node files, which matches
how the package is shipped and loaded by `n8n`.

The `test:coverage` command now uses the same `98%` line-coverage threshold as
the Python package coverage checks. The explicit `python-threshold` command is
now an alias for that same enforced gate.

If you update `n8n-workflow` again, keep this compatibility split in mind:

- Node `22` and Node `24` currently support the published dependency chain
   without extra package overrides
- Node `26` currently depends on the local `isolated-vm` override until the
   published `n8n-workflow` dependency chain moves past `isolated-vm` `6.x`

## Local n8n Development Instance

The repository includes a manual-start local n8n instance for runtime node validation.

Unlike the packaged `.tgz` distribution flow, this development instance stages a
package-shaped directory under:

```text
.devcontainer/development/n8n/custom/node_modules/n8n-nodes-ticket-system-mock/
```

That staged directory currently contains:

- `package.json`
- `dist/`

The same local compose profile also starts the official `n8nio/runners` sidecar
so contributor workflows can execute both JavaScript and Python Code nodes.

This layout follows the package-mounting approach commonly used in the n8n
community for local node building with Docker. The development compose file mounts
that directory directly into the container under `~/.n8n/custom/node_modules/`.

Use these commands from the repository root:

```bash
make update-devserver
make n8n-node-stage-dev-package
./scripts/run_n8n_smoke_test.bash start
./scripts/run_n8n_smoke_test.bash reload
```

Use `make update-devserver` when you want one command that refreshes the Python
SDK download, refreshes the downloadable n8n package in `build/integrations/`,
refreshes the local n8n development mount, and restarts the web application
development server.

Use `start` the first time. Use `reload` after code changes when you want to rebuild
the staged package and recreate the running n8n container so updated package
mounts and assets are applied.

## Pack and Stage the Node

To generate the installable package artifact, run:

```bash
cd src/n8n_node
npm run pack:node
```

This command:

1. runs the normal build
2. creates the local `build/` directory when needed
3. writes an npm package file into `src/n8n_node/build/`

That `.tgz` file is the source artifact used to populate the standard custom
node directory layout in `n8n`.

For local development-server delivery, the helper script moves the generated
package file from `src/n8n_node/build/` into `build/integrations/`, which is
one of the directories the web application already scans for the downloadable
n8n package.

For runtime use in `n8n`, extract that package file into:

```text
~/.n8n/custom/node_modules/n8n-nodes-ticket-system-mock/
```

The final directory on the `n8n` host should contain the package files,
including `package.json` and `dist/`.

## How the Webapp Image Bundles the Package

The webapp container build includes a dedicated Node-based builder stage for the
n8n package.

That builder stage now uses Node `22` to match the devcontainer baseline. This
keeps the shipped package build path aligned with local contributor tooling and
removes one blocker for future `n8n-workflow` upgrades that no longer install
cleanly on Node `20`.

The build flow is:

1. the Dockerfile copies `src/n8n_node/package*.json` into the builder stage
2. the builder stage runs `npm ci`
3. the full `src/n8n_node` directory is copied into the builder stage
4. the builder stage runs `npm run pack:node`
5. the resulting `.tgz` file is copied into `/tmp/n8n-node-package`
6. the final Python webapp image copies that directory into
   `/app/build/integrations`

This keeps Node.js out of the final runtime image while still shipping the n8n
package with the deployment.

The bundled artifact is then available to the web application so users can
download it from the authenticated `Integrations` page and place it into the
standard `~/.n8n/custom/node_modules/` installation path.

## Recommended Contributor Workflow

Use this sequence when changing the n8n package:

1. update the node code only inside `src/n8n_node`
2. run `make n8n-node-build`
3. run `make n8n-node-lint` and `make n8n-node-test` for the fast local
   validation loop
4. run `make n8n-node-test-coverage` when the change affects shipped behavior or
   when you need the repository coverage gate
5. run `make update-devserver` when you want to refresh all local development
   server artifacts in one step, or run `make n8n-node-stage-dev-package` alone
   when only the local n8n development mount needs to change
6. run `make n8n-node-pack` if the package artifact or distribution path changed
7. run repository validation such as `make check` and `make test` when the
   change affects shipped behavior
8. if the change affects runtime installation or delivery, verify the webapp
   image still contains the packaged file under `/app/build/integrations`
9. update the relevant n8n reference docs under `docs/external/n8n/` and the
   user guide when operator behavior changed

The repository-level `make check` target now includes the n8n package build,
lint, unit-test, and package-validation steps. The repository-level `make test`
target now includes the n8n package coverage gate alongside the Python coverage
commands.

If the change came from a webapp-side contract update, also verify the current
REST list envelope and webhook body contract end to end. In the current
repository contract, list endpoints deliver their result arrays under a root
`data` key, and webhook bodies expose the triggering action under root `event`
while storing the emitted Issue snapshot under root `data`.

If the change affects workflow behavior, trigger behavior, or credential setup,
also validate the package in a real n8n instance before treating the work as
complete.

## Related Documents

- [n8n Custom Node Development](../external/n8n/README.md)
- [n8n Implementation Reference](../external/n8n/implementation-reference.md)
- [n8n Testing and Distribution](../external/n8n/testing-and-distribution.md)
- [n8n Integration Guide](../user/n8n-integration.md)
- [Local Build And Production Test Verification](local-build-and-production-test-verification.md)
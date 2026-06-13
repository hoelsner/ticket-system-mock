# n8n Local Smoke Test

## Purpose

This guide documents a contributor-friendly smoke test for the local n8n node package.
It uses a manually started Dockerized n8n instance that joins the same development
network as the webapp, so n8n can call the local API at `http://webapp:8000`.

The local development instance follows the package-style mounting approach described in the
n8n community node-building guidance: the repository stages a package-shaped directory and
mounts it into `.n8n/custom/node_modules/n8n-nodes-ticket-system-mock` inside the container.

The n8n service is intentionally excluded from the default devcontainer startup.
Contributors start it only when they need runtime verification.

## Table Of Contents

1. [Prerequisites](#prerequisites)
2. [Start The Local n8n Instance](#start-the-local-n8n-instance)
3. [Confirm That The Custom Nodes Loaded](#confirm-that-the-custom-nodes-loaded)
4. [Smoke Test The Action Nodes](#smoke-test-the-action-nodes)
5. [Smoke Test The Poll Trigger](#smoke-test-the-poll-trigger)
6. [Smoke Test The Webhook Trigger](#smoke-test-the-webhook-trigger)
7. [Stop Or Reset The Instance](#stop-or-reset-the-instance)

## Prerequisites

- Start the regular development stack first so the `webapp` service is available.
- Run the commands from the repository root inside the development container.
- Keep in mind that the n8n container reaches the API through `http://webapp:8000`,
  not `http://localhost:8000`.

## Start The Local n8n Instance

Use the helper script to build the local node package and start the profile-gated
n8n service:

```bash
./scripts/run_n8n_smoke_test.bash start
```

This command does the following:

1. Runs `./scripts/build_n8n_dev_package.bash` to build the node and stage a local package directory.
2. Starts the `n8n` and `n8n-runners` services from `.devcontainer/development/docker-compose.yml` with the `n8n` profile.
3. Exposes the editor on `http://localhost:5678`.

The local profile uses the official external task runner sidecar so both JavaScript
and Python Code nodes can execute during runtime verification.

On first startup, open `http://localhost:5678` in your browser and complete the
owner account setup for the local instance.

## Confirm That The Custom Nodes Loaded

The compose service mounts the staged package directory into
`/home/node/.n8n/custom/node_modules/n8n-nodes-ticket-system-mock`, which matches the
package-style custom node setup commonly used for local n8n node development. After login:

1. Create a new workflow.
2. Add a node.
3. Search for `Ticket System Mock`.

You should see these custom nodes:

- `TSM - Reference Data`
- `TSM - Collection`
- `TSM - Category`
- `TSM - Issue`
- `TSM - Issue Attachment`
- `TSM - Issue Activity`
- `TSM - Issue Poll Trigger`
- `TSM - Issue Webhook Trigger`

If they do not appear, rebuild and recreate the service so Docker reapplies the
staged package mount:

```bash
./scripts/run_n8n_smoke_test.bash reload
```

## Smoke Test The Action Nodes

Create a credential for the custom nodes with these values:

- Base URL: `http://webapp:8000`
- Username and password: use a valid local application account

Use the container-visible service URL exactly as shown above. Do not use
`http://localhost:8000` inside the n8n credential, because `localhost` would
refer to the n8n container itself instead of the webapp service.

Then verify a simple read and write flow:

1. Add a `TSM - Reference Data` node and fetch one simple list, such as users.
2. Add a `TSM - Collection` or `TSM - Category` node and fetch one reference list.
3. Add a `TSM - Issue` node and create a test issue in a known collection and category.
4. Add a `TSM - Issue Activity` node and post a comment to that new issue.
5. Add a `TSM - Issue Attachment` node and upload one attachment to that same issue.
6. Confirm the new issue, comment, and attachment in the web application.

This smoke test proves that authentication, request construction, and response
mapping all work against the running API.

For the list-oriented nodes, confirm that the workflow output already contains
the returned entities directly. The REST API now wraps list endpoint results
under a root `data` key, and the bundled n8n nodes unwrap that envelope before
emitting items into the workflow.

If the credential is misconfigured, the node should now report a clearer cause.
Examples include an invalid Base URL format, an unreachable host, `401`
authentication failures, or `403` permission failures.

## Smoke Test The Poll Trigger

Verify that the polling trigger can detect newly created issues:

1. Create a workflow that starts with `TSM - Issue Poll Trigger`.
2. Configure a short polling interval and enable full issue detail loading.
3. If needed, use the built-in `Priority` and `Workflow State` select fields to
    limit the poller without typing raw codes manually.
4. Add a terminal node such as `No Operation, do nothing`.
5. Activate the workflow.
6. Create a fresh issue in the webapp.
7. Confirm that the new execution in n8n contains that issue.

By default, the first poll emits the currently matching issues and sets the
watermark. If you disable `Emit Existing Issues On First Poll`, the first poll
only establishes the watermark and later polls emit newly changed issues.

## Smoke Test The Webhook Trigger

The local compose setup publishes webhook URLs using the internal service host
`http://n8n:5678/` so the webapp container can reach the trigger endpoint across
the shared development network.

To verify the webhook trigger:

1. Create a workflow that starts with `TSM - Issue Webhook Trigger`.
2. Copy the test webhook URL from the node.
3. Configure the web application to send one supported issue event to that URL.
4. Trigger the matching event in the webapp.
5. Confirm that n8n receives the payload, that the body includes root `event`
    and `data` fields, and that `webhook_metadata` is present in the output.

Because the webhook URL uses the internal `n8n` hostname, this test is intended
for service-to-service delivery from the local application stack, not for manual
browser submission from the host machine.

## Stop Or Reset The Instance

Use the helper script to manage the local n8n instance:

```bash
./scripts/run_n8n_smoke_test.bash stop
./scripts/run_n8n_smoke_test.bash logs
./scripts/run_n8n_smoke_test.bash down
./scripts/run_n8n_smoke_test.bash reload
```

Use `down` when you need to remove the local instance entirely. Use `reload`
when you changed the node package and want to rebuild the staged package and
recreate the running n8n container with the current compose mounts.
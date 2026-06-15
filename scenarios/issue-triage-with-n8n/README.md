# Issue Triage With n8n

Use this scenario to prepare a Ticket System Mock instance for an issue triage
demo that hands work to n8n.

## What You Get

After the script finishes, the instance contains:

- groups for `IT Operations`, `Agent Escalation (HITL)`, and `Agents > Triage`
- users `demo`, `user`, and `triage_agent`
- active collections `Infrastructure Operations` and `Test`
- active scenario issue categories
- a workflow-state auto-assignment rule for `New`

The authenticated superuser you use to run the script is kept. Other existing
instance data is removed during the reset.

## Prerequisites

1. Start the target Ticket System Mock instance.
2. From the repository root, create or refresh the scenarios environment:

   ```bash
   cd scenarios
   uv sync --python 3.14
   cd ..
   ```

3. Make sure you have a superuser username and password for the target
   instance.

## Run The Scenario

From the repository root, run:

```bash
scenarios/.venv/bin/python scenarios/issue-triage-with-n8n/seed.py --base-url http://webapp:8000 --username admin
```

You can also provide credentials through environment variables:

```bash
export TSM_BASE_URL=http://webapp:8000
export TSM_USERNAME=admin
export TSM_PASSWORD=your-password
scenarios/.venv/bin/python scenarios/issue-triage-with-n8n/seed.py
```

If you do not pass `--password` and `TSM_PASSWORD` is not set, the script asks
for the password securely in the terminal.

When the script prints the reset summary, type `RESET` to continue.

## What Happens During The Run

1. The script signs in with the provided superuser account.
2. It shows how much data will be removed.
3. It waits for your explicit reset confirmation.
4. It clears the instance while preserving the authenticated superuser.
5. It seeds the triage groups, users, collections, categories, and workflow
   rule.

## After The Seed

Open the application and verify that the triage users and categories are
present. If you want the full n8n demo flow, import the workflow asset from the
`assets/` directory and complete the webhook-side configuration in n8n.

The seed script creates these application users:

- `demo` with password `demo1234`
- `user` with password `user1234`
- `triage_agent` with password `triage1234`

The `triage_agent` user is created as a system user with image avatars enabled,
so the application renders the default agent avatar image
`default_avatar_agent.png` for that account.

## Assets

See `assets/` for scenario-specific files used with the n8n part of the demo.
# Ticket System Mock n8n Nodes

Private n8n node package for the Ticket System Mock REST API.

## Current Status

This package now contains the initial self-contained scaffold:

- TypeScript build and pack scripts
- shared HTTP Basic credential
- `TSM - Reference Data` node for system, profile, groups, users, collections, and categories
- `TSM - Issue` node for list, detail, create, update, archive, and move
- `TSM - Issue Activity` node for comment create/update and attachment create/update/delete
- `TSM - Issue Poll Trigger` node for polling issue updates through `/api/issues`
- `TSM - Issue Webhook Trigger` node for receiving outbound webhook deliveries from the application

## Build

```bash
npm install
npm run build
```

## Export

```bash
npm run pack:node
```

This writes an installable npm tarball to `src/n8n_node/build/`.
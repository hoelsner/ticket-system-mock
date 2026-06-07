---
name: queue-runner
description: 'Process queued task files from .queue/ directory one-by-one. Use when: running queued tasks, processing task queue, batch task execution, working through .queue files.'
argument-hint: 'Optional: filename filter or "status" to list pending tasks'
disable-model-invocation: true
user-invocable: true
---

# Queue Runner

Execute `.md` files from the `.queue/` directory as individual tasks, processing them sequentially in numeric-prefix order. If it is a directory, treat all files within the directory as part of the same task and execute them together. Start with the `TASK.md`, `SPEC.md` or `README.md` file as the main instruction, and use the other files as additional context. After successful execution, move the task file to `.queue/done/`.

## When to Use

- The user says "run the queue", "process tasks", or "work through the queue"
- The user invokes `/queue-runner`

## Queue Layout

```
.queue/
├── 01-some-task.md
├── 02-another-task
│   ├── TASK.md
│   ├── additional_context.md
├── 03-third-task.md
└── done/
    └── 01-completed-task.md
```

## Task File Format

Each `.md` file in `.queue/` is a plain markdown body treated as a user prompt. The filename determines execution order via numeric prefix (e.g., `01-`, `02-`).

No frontmatter is required. The entire file content is the task instruction.

## Procedure

### 1. Discover Tasks

List all `.md` files and directories (except the `.queue/done/` directory) directly in `.queue/` (not in subdirectories). Sort them by filename (numeric prefix determines order). If no files are found, report that the queue is empty and stop.

### 2. Present Queue Summary and Confirm Mode

Before executing anything, show the user:
- Number of pending tasks
- Ordered list of filenames with a one-line summary of each (first non-empty line or first 80 characters)

Then ask the user to choose an execution mode:
- **Run all** — execute every task sequentially without per-task confirmation (stop only on failure)
- **Step-by-step** — confirm each task individually before execution
- **Abort** — cancel without executing anything

### 3. Process Each Task Sequentially

Tasks may depend on earlier tasks in the queue (they share workspace state). Always execute in order.

For each task file, in order:

1. **Read** the file content
2. **Plan** — interpret the body as a user request and produce a concrete action plan. Present the plan to the user with the task filename as heading.
3. **Confirm** (step-by-step mode only) — ask the user to approve, skip, or abort the queue. In run-all mode, proceed immediately.
4. **Execute** — carry out the plan following the same approach as if the user had typed the message directly
5. **Complete** — move the file to `.queue/done/` (create the directory if it doesn't exist)
6. **Report** — briefly confirm completion before moving to the next task

### 4. Handle Failures

If a task fails or is ambiguous (in either mode):
- Stop processing the queue immediately
- Present the failure details and the task file content to the user
- Ask the user whether to: retry the task, skip it and continue, or abort the queue
- Do not proceed to subsequent tasks until the user responds

### 5. Final Summary

After all tasks are processed (or the queue is aborted), report:
- Tasks completed
- Tasks skipped
- Tasks remaining

Move the processed files to `.queue/done/` and leave any skipped or unprocessed files in `.queue/` for future runs.

## Status Check

If the user passes "status" as an argument, skip execution and only report:
- Pending tasks (count and filenames)
- Completed tasks in `.queue/done/` (count)

## Rules

- Never execute tasks out of order — later tasks may depend on earlier ones
- In step-by-step mode, never proceed without user confirmation per task
- In run-all mode, proceed automatically but always stop on failure
- Respect all workspace instructions (AGENTS.md, .instructions.md) during task execution
- If a task references files or services, verify they exist before planning
- The `.queue/done/` directory should be created automatically when the first task completes

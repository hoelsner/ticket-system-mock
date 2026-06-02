---
name: add-webapp-python-dependency
description: 'Add a Python dependency to the Django webapp using the repository workflow. Use when adding a new webapp package, updating webapp dependency pins, or preparing a dependency change in src/webapp with uv, requirements.in, and requirements.txt.'
argument-hint: 'Describe the dependency to add, whether it is runtime or development-only, and whether approval has already been given'
user-invocable: true
---

# Add Webapp Python Dependency

## What This Skill Does

This skill applies the repository-specific workflow for adding a Python dependency to the Django web application in `src/webapp`.

It keeps dependency changes consistent with the project rules:

1. do not add a dependency without confirmation
2. edit `src/webapp/requirements.in` with a major-minor pin - check with pypi if the version and dependency exists
3. regenerate `src/webapp/requirements.txt` with `uv pip compile`
4. install the resolved dependencies into `src/webapp/.venv`
5. verify the dependency change in the narrowest relevant way

## When to Use

Use this skill when:

- a new Python package must be added to the Django webapp
- an existing webapp dependency pin needs to change
- the user asks to install a package for code under `src/webapp`
- a webapp tool such as `coverage`, `bandit`, or another Python package must become part of the managed dependency set

Do not use this skill when:

- the package is for the devcontainer image only rather than the Django webapp
- the change is for a different component outside `src/webapp`
- the user has not confirmed the dependency should be added

## Repository-Specific Facts

- the managed input file is `src/webapp/requirements.in`
- the compiled lock-style output is `src/webapp/requirements.txt`
- the webapp virtual environment is `src/webapp/.venv`
- the compile command is `uv pip compile --output-file requirements.txt requirements.in`
- the install command is `uv pip install -r requirements.txt`

## Procedure

1. Confirm the dependency change is approved.
2. Classify the dependency:
   - if it is needed by the Django webapp at runtime or during webapp development tasks, keep it in `src/webapp`
   - if it is only for the devcontainer image or general workspace tooling, do not use this workflow
3. Read `src/webapp/AGENTS.md`, `src/webapp/requirements.in`, and `src/webapp/requirements.txt` if they are not already in context.
4. Add the dependency to `src/webapp/requirements.in` using a major-minor pin, for example `package>=1.2,<1.3`.
5. Recompile from within `src/webapp`:

```bash
uv pip compile --output-file requirements.txt requirements.in
```

6. Install into the existing webapp virtual environment from within `src/webapp`:

```bash
uv pip install -r requirements.txt
```

7. Run the narrowest relevant validation:
   - import check if the package is only needed as a tool or module presence check
   - the specific script or make target that depends on the package if one exists
   - otherwise a minimal command that proves the dependency is available in `src/webapp/.venv`
8. Summarize which files changed, what was installed, and what validation ran.

## Decision Points

### Approval Gate

- If the user has not explicitly approved adding the dependency, stop and ask first.
- If approval is already present in the conversation, proceed without re-asking.

### Scope Gate

- If the dependency is for `src/webapp`, use this workflow.
- If the dependency belongs to `.devcontainer/requirements.txt` or another component, route to that dependency workflow instead of editing `src/webapp/requirements.in`.

### Pinning Rule

- Default to a major-minor bounded pin like `>=X.Y,<X.(Y+1)`.
- Do not use an unbounded dependency unless the user explicitly requests it.

### Validation Rule

- Prefer the smallest executable validation that proves the dependency is installed and usable.
- If the dependency was added to support an existing script or Make target, run that exact script or target.

## Quality Criteria

The task is complete when:

- the dependency was approved before being added
- `src/webapp/requirements.in` contains the intended major-minor pin
- `src/webapp/requirements.txt` was regenerated from that input file
- `src/webapp/.venv` has the resolved dependency installed
- at least one focused validation step passed
- the final report states any remaining risk or missing follow-up clearly

## Output Expectations

When using this skill, produce:

1. the dependency decision and scope
2. the exact pin added to `requirements.in`
3. confirmation that `requirements.txt` was recompiled
4. confirmation that dependencies were installed into `src/webapp/.venv`
5. the validation command and outcome

## Example Prompts

- `/add-webapp-python-dependency Add django-debug-toolbar to the webapp. Approval is already given.`
- `/add-webapp-python-dependency Add bandit to the webapp dependency set and validate the bandit make target.`
- `/add-webapp-python-dependency Update coverage to the next minor line for src/webapp and rerun the coverage test target.`

## Non-Goals

- deciding whether a dependency is architecturally appropriate without user confirmation
- managing devcontainer-only packages in `.devcontainer/requirements.txt`
- refactoring application code unrelated to making the dependency usable
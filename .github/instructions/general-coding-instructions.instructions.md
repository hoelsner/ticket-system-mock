---
description: This file describes the coding style and best practices for the project
# apply to python, html, js, css files in the src/webapp directory
applyTo: src/webapp/**/*.{py,html,js,css}
---

When developing code, use the following workflow to ensure that your code is clean, maintainable, and adheres to the project's standards:

## Development Workflow

1. Understand the problem and desired outcome

- If you see a potential improvement, mention it - don't implement it without confirmation.

2. Collect all relevant information and clarify any ambiguities with the user

- If you need additional information, look at `docs/architecture` and `docs/external`
- If you notice a bug, mention it - don't fix it without confirmation.

3. Break down the problem into smaller, manageable tasks
4. based on the karpathy-guidelines, write clean, modular code that follows the project's style and guidelines
5. Test your code thoroughly, including edge cases and error handling
6. after each task, run the following commands to check for linting errors and run tests:

```bash
make check
```

If you encounter errors, fix them before proceeding to the next task.

7. after completing all tasks, run the following command to check for linting errors, run tests, and generate a coverage report:

```bash
make check
make test
```

If you encounter errors, fix them before proceeding to the next step.

8. Document your code and any important decisions or assumptions
9. check for documentation drift and update the documentation if needed
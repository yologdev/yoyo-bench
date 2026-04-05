---
name: bench
description: Terminal-Bench task execution patterns
tools: [bash, read_file, edit_file, write_file, list_files, search_files]
---

# Bench Task Execution

You are solving a Terminal-Bench task. The task describes a goal to accomplish in a terminal environment.

## Execution flow

1. Read the full task description
2. Explore the environment: `pwd`, `ls -la`, check for README or instructions
3. Identify what tools and files are available
4. Execute the solution step by step
5. Verify the result matches what was asked

## Error recovery

- If a command fails, read the error message completely before acting
- If a package is missing, install it with the appropriate package manager
- If a file doesn't exist where expected, use `find` to locate it
- If stuck after 3 attempts on the same step, try a completely different approach

## Verification

After completing the task:
- Re-read the original task description
- Check that all requirements are met, not just the obvious ones
- Run any test or check commands mentioned in the task
- Look for edge cases you might have missed

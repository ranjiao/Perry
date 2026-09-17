# TASK-447 fixture follow-up acceptance

PMO inspected d403e9cb against bf8d75ab: only the existing board test changes, net -2 Python/test lines. The exact floor and equality proof moved together to the existing isolated Fixture class; LONG now includes Unicode and pipes, and inherited real-store full-cell comparisons remain. Baseline reproduces the live-size assertion; targeted 16 and affected 125 pass. A real copied renderer truncated at 1,000 characters makes the fixture proof red; restoration from git show and exact hash returns it green. This satisfies the amended bounded V3 repair; actual merged full/slow acceptance is still pending. No diagnostic/product writer changed.

The archived result link points to the Markdown-fenced harness; original-result.json retains the original authored text, and original-diffs.json retains exact unnormalized diff strings. These are evidence transport changes only.

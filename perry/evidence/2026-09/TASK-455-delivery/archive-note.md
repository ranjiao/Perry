# Diff preservation

The `.diff` files are readable copies with trailing whitespace normalized for the repository whitespace gate. `original-diffs.json` retains each original diff string exactly, including blank context-line prefixes and final newlines; decode it to reproduce the exact original bytes. Immutable base/head and fixture metadata remain in the review/result.

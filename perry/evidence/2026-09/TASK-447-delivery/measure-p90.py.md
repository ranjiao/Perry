# Retained evidence harness

```python
"""Measure a complete perry-task list --json capture; never interpret its prose."""
import json
import math
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text())
assert not payload['bound']['truncated'], 'Re-read the complete open contract'
rows = [r for r in payload['tasks'] if r['open']]
assert len(rows) == payload['bound']['open_total'], 'Incomplete open rows'
lengths = sorted(len(r['next_action']) for r in rows)
print(json.dumps({'open_rows':len(rows), 'unit':'Unicode code points',
                  'method':'nearest rank: sorted lengths[ceil(0.9*n)-1]',
                  'p90':lengths[math.ceil(.9*len(rows))-1] if rows else None,
                  'maximum':max(lengths) if rows else None}))

```

# Retained measurement or mutation harness

```python
from pathlib import Path
import json
root = Path(__file__).parent
names = ['before.txt', 'normal.initial.txt', 'busy.initial.txt', 'unknown.initial.txt', 'safety.initial.txt']
receipts = []
for name in names:
    text = (root / name).read_text()
    row = {'path': name, 'lines': len(text.splitlines()), 'unicode_characters': len(text), 'utf8_bytes': len(text.encode()), 'within_budget': len(text.splitlines()) <= 12 and len(text) <= 1200}
    receipts.append(row)
    if name != 'before.txt':
        assert row['within_budget'], row
mutations = root / 'mutations'
mutations.mkdir(exist_ok=True)
# Exact supplied-string mutations of agent-authored prose; no semantic classifier.
original = (root / 'busy.details.md').read_text()
omit = '- USER-006 “Choose language”: Choose English or Chinese.\n'
assert omit in original
(mutated := mutations / 'omitted-pending.details.md').write_text(original.replace(omit, ''))
original = (root / 'unknown.details.md').read_text()
omit = 'Unknown history.latest_weekly — Report source unavailable\n'
assert omit in original
(mutations / 'omitted-unknown.details.md').write_text(original.replace(omit, ''))
original = (root / 'normal.initial.txt').read_text()
(mutations / 'oversized.initial.txt').write_text(original + ('Additional note.\n' * 80))
for name in ['oversized.initial.txt']:
    text = (mutations / name).read_text()
    row = {'path': 'mutations/' + name, 'lines': len(text.splitlines()), 'unicode_characters': len(text), 'utf8_bytes': len(text.encode()), 'within_budget': len(text.splitlines()) <= 12 and len(text) <= 1200}
    assert not row['within_budget']
    receipts.append(row)
(root / 'measurements.json').write_text(json.dumps(receipts, indent=2)+'\n')
print(json.dumps(receipts, indent=2))

```

from pathlib import Path
p=Path(__file__).parents[1]/'docs/art/source.txt'
assert p.read_text() == 'synthetic source A\n'
print('custom source criterion passed; integration and human review not checked')

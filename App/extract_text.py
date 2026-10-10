import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
data = open('extracted_wiz.json', encoding='utf-8').read()
strings = re.findall(r'\"([^\"]{30,})\"', data)

# Filter for human readable text
results = []
for s in strings:
    if ' ' in s and not s.startswith('http') and not s.startswith('<') and not s.startswith('//') and '{' not in s:
        # Ignore things like CSS or minified JS
        if '--mat-' not in s and 'font-' not in s:
            results.append(s)

for r in results:
    print("MATCH: " + r)

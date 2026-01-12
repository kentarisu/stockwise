import re
import os

file_path = r'c:\Users\Orly\stockwise\templates\dashboard_full.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Merge all {% ... %}
content = re.sub(r'\{%(.*?)%\}', lambda m: '{%' + m.group(1).replace('\n', ' ').replace('\r', ' ') + '%}', content, flags=re.DOTALL)
# Merge all {{ ... }}
content = re.sub(r'\{\{(.*?)\}\}', lambda m: '{{' + m.group(1).replace('\n', ' ').replace('\r', ' ') + '}}', content, flags=re.DOTALL)

# Fix double close tags if any were introduced by previous mangled edits
content = content.replace('%} %}', '%}')
content = content.replace('}} }}', '}}')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Aggressive tag fix complete.")

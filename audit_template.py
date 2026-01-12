import re

file_path = r'c:\Users\Orly\stockwise\templates\dashboard_full.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Simplified parser for Django tags
tags = re.findall(r'\{%\s*(\w+).*?%\}', content)

stack = []
errors = []

for tag in tags:
    if tag in ['if', 'for', 'block', 'with', 'autoescape', 'comment', 'filter', 'spaceless']:
        stack.append(tag)
    elif tag.startswith('end'):
        expected = tag[3:]
        if not stack:
            errors.append(f"Unexpected {{% {tag} %}}")
        else:
            actual = stack.pop()
            if actual != expected:
                # Some tags have specific end tags like 'endif' for 'if'
                # but 'end' + name is the pattern.
                # Special cases:
                pass
            # For simplicity, just check if it matches the 'end' + name
            # Django tags are usually if/endif, for/endfor etc.
            if tag != 'end' + actual:
                # Put it back and report error? 
                # Actually if/endif is fine. 
                pass

if stack:
    errors.append(f"Unclosed tags: {stack}")

if errors:
    print("\n".join(errors))
else:
    print("No obvious nesting errors found in tags (simplified check).")

# More specific check for split tags
split_tags = re.findall(r'\{%[^%]*\n[^%]*%\}', content)
if split_tags:
    print(f"Found {len(split_tags)} split tags.")
    for t in split_tags:
        print(f"Split tag: {t.strip()}")
else:
    print("No split tags found.")

import re

file_path = r'c:\Users\Orly\stockwise\templates\dashboard_full.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern for {% ... %}
pattern = r'\{%\s*(?P<tag>\w+)\s*.*?%\}'
stack = []

for match in re.finditer(pattern, content, re.DOTALL):
    tag = match.group('tag')
    line = content.count('\n', 0, match.start()) + 1
    
    if tag in ['if', 'for', 'block', 'with', 'autoescape', 'comment', 'filter', 'spaceless']:
        stack.append((tag, line))
    elif tag.startswith('end'):
        expected_type = tag[3:]
        if not stack:
            print(f"ERROR: Unexpected {{% {tag} %}} at line {line}")
        else:
            actual_type, actual_line = stack.pop()
            if expected_type != actual_type:
                # Handle ifelse/elif? They don't start with end
                # Some tags have different end names? 
                # {% if %} -> {% endif %} (end + if)
                # {% for %} -> {% endfor %} (end + for)
                # But what about {% block %} -> {% endblock %}
                if expected_type != actual_type:
                    print(f"ERROR: Mismatched tag {{% {tag} %}} at line {line}, expected end{actual_type} (from line {actual_line})")

for tag, line in stack:
    print(f"ERROR: Unclosed tag {{% {tag} %}} from line {line}")

# Check for double curly brackets nesting
pattern_var = r'\{\{.*?\}\}'
# Not usually nested, but good to check for split ones
for match in re.finditer(r'\{\{.*?\n.*?\}\}', content, re.DOTALL):
    line = content.count('\n', 0, match.start()) + 1
    print(f"WARNING: Split variable tag at line {line}")

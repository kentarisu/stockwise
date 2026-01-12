import re

file_path = r'c:\Users\Orly\stockwise\templates\dashboard_full.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

stack = []
split_tags = []

for i, line in enumerate(lines):
    line_num = i + 1
    # Find all tags in this line
    tags = re.findall(r'\{%\s*(\w+).*?%\}|(\{\%.*?$)', line)
    # This regex is simplified and might miss complex cases, but let's try.
    
    # Actually, let's use a full file search with line number tracking
    pass

full_content = "".join(lines)
matches = re.finditer(r'\{%\s*(?P<tag>\w+).*?%\}', full_content, re.DOTALL)

for m in matches:
    tag_name = m.group('tag')
    start_pos = m.start()
    line_no = full_content.count('\n', 0, start_pos) + 1
    
    if tag_name in ['if', 'for', 'block', 'with', 'autoescape', 'comment', 'filter', 'spaceless']:
        stack.append((tag_name, line_no))
    elif tag_name.startswith('end'):
        expected_base = tag_name[3:]
        if not stack:
            print(f"Error: Unexpected {{% {tag_name} %}} at line {line_no}")
        else:
            actual_base, actual_line = stack.pop()
            if tag_name != 'end' + actual_base:
                # Handle ifelse/elif? No, those don't start with 'end'
                # Re-push? 
                print(f"Error: Mismatched tag {{% {tag_name} %}} at line {line_no}, expected end{actual_base} (from line {actual_line})")

for tag, line in stack:
    print(f"Error: Unclosed tag {{% {tag} %}} from line {line}")

# Split tags check
for m in re.finditer(r'(\{%.*?\n.*?%\})|(\{\{.*?\n.*?\}\})', full_content, re.DOTALL):
    line_no = full_content.count('\n', 0, m.start()) + 1
    content = m.group(0).replace('\n', '\\n')
    print(f"Split tag at line {line_no}: {content}")

import os
import re

TARGET_DIR = r"e:\CounterFlow\ANTIGRAVCFT1\CounterFlow\app"

# Match setColumnWidth calls: e.g. .setColumnWidth(0, 90) -> .setColumnWidth(0, 120)
re_col = re.compile(r'(\.setColumnWidth\(\s*\d+\s*,\s*)(\d+)(\s*\))')

INCREMENT = 35

changed_files = 0
for root, dirs, files in os.walk(TARGET_DIR):
    for file in files:
        if not file.endswith('.py'):
            continue
            
        path = os.path.join(root, file)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        def replace_col(match):
            val = int(match.group(2))
            # Only increment widths reasonably larger than a checkbox column
            if val > 40:
                new_val = val + INCREMENT
                return f"{match.group(1)}{new_val}{match.group(3)}"
            return match.group(0)
            
        content = re_col.sub(replace_col, content)
        
        if content != original_content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated column widths in {file}")
            changed_files += 1

print(f"Total files updated for column widths: {changed_files}")

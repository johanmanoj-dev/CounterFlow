import os
import re

TARGET_DIR = r"e:\CounterFlow\ANTIGRAVCFT1\CounterFlow\app"

# Match layout fixed heights like .setFixedHeight(40) or .setMinimumHeight(40)
# This finds calls setting heights >= 20 and adds 6px to them
re_height = re.compile(r'(\.(?:setFixedHeight|setMinimumHeight|setHeight)\()(\d+)(\))')

INCREMENT = 6

changed_files = 0
for root, dirs, files in os.walk(TARGET_DIR):
    for file in files:
        if not file.endswith('.py'):
            continue
            
        path = os.path.join(root, file)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        def replace_height(match):
            val = int(match.group(2))
            if val >= 20: # only scale up text boxes/buttons, not small divider lines of 1px
                new_val = val + INCREMENT
                return f"{match.group(1)}{new_val}{match.group(3)}"
            return match.group(0)
            
        content = re_height.sub(replace_height, content)
        
        if content != original_content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated heights in {file}")
            changed_files += 1

print(f"Total files updated for heights: {changed_files}")

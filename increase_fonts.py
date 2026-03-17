import os
import re

TARGET_DIR = r"e:\CounterFlow\ANTIGRAVCFT1\CounterFlow\app"

# Matches: font-size: 13px  or  font-size: 13px;
re_font_size = re.compile(r'(font-size:\s*)(\d+)(px)')
# Matches: QFont("Segoe UI", 20)  or  QFont("Segoe UI", 13, QFont.Weight.Bold)
re_qfont = re.compile(r'(QFont\([^,]+,\s*)(\d+)(\s*[,)])')

INCREMENT = 3

changed_files = 0
for root, dirs, files in os.walk(TARGET_DIR):
    for file in files:
        if not file.endswith('.py'):
            continue
            
        path = os.path.join(root, file)
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        def replace_px(match):
            new_val = int(match.group(2)) + INCREMENT
            return f"{match.group(1)}{new_val}{match.group(3)}"
            
        content = re_font_size.sub(replace_px, content)
        
        def replace_qfont(match):
            new_val = int(match.group(2)) + INCREMENT
            return f"{match.group(1)}{new_val}{match.group(3)}"
            
        content = re_qfont.sub(replace_qfont, content)
        
        if content != original_content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated {file}")
            changed_files += 1

print(f"Total files updated: {changed_files}")

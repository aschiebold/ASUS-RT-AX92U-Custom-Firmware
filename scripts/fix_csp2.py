#!/usr/bin/env python3
filepath = "/home/user/asuswrt/release/src/router/httpd/httpd.c"
with open(filepath, "r") as f:
    lines = f.readlines()

csp_value = 'Content-Security-Policy: default-src \'self\'; script-src \'self\' \'unsafe-inline\' \'unsafe-eval\'; style-src \'self\' \'unsafe-inline\'; img-src \'self\' data: blob:; connect-src \'self\'; font-src \'self\' data:; worker-src \'self\' blob:; child-src \'self\' blob:; frame-src \'self\''
good_line = '        (void) fprintf( conn_fp, "' + csp_value + '\\r\\n");\n'

i = 0
fixed = 0
while i < len(lines):
    if 'Content-Security-Policy' in lines[i]:
        lines[i] = good_line
        # Remove stray next line if it's the broken fragment
        if i + 1 < len(lines) and lines[i+1].strip() in ['\\n");', '']:
            lines.pop(i + 1)
        fixed += 1
        print(f"Fixed line {i+1}")
    i += 1

with open(filepath, "w") as f:
    f.writelines(lines)
print(f"Done, fixed {fixed} lines")

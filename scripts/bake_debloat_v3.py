#!/usr/bin/env python3
"""Patch remaining function definitions with early returns."""

SERVICES = "/home/user/asuswrt/release/src/router/rc/services.c"

with open(SERVICES, 'r') as f:
    lines = f.readlines()

# Functions to make no-op, with their return type
void_funcs = [
    'void start_amas_lanctrl(void)',
    'void start_ahs(void)',
    'void start_amas_ssd(void)',
    'void start_amas_status(void)',
    'void start_amas_misc(void)',
    'void start_amas_bhctrl(void)',
    'void start_amas_wlcconnect(void)',
    'void start_diskmon(void)',
]

int_funcs = [
    'int start_netool(void)',
    'int start_infosvr()',
    'int start_ptcsrv(void)',
]

changes = []

for i, line in enumerate(lines):
    stripped = line.strip()

    # Check if this line is a function definition we want to patch
    for func_sig in void_funcs:
        if stripped == func_sig:
            # Next line should be '{'
            if i + 1 < len(lines) and lines[i+1].strip() == '{':
                # Check if already patched
                if i + 2 < len(lines) and 'DEBLOAT' in lines[i+2]:
                    break
                # Insert return after the brace
                lines.insert(i + 2, '\treturn; /* DEBLOAT */\n')
                changes.append(f"{func_sig.split('(')[0].split()[-1]}() -> void no-op")
            break

    for func_sig in int_funcs:
        if stripped == func_sig:
            if i + 1 < len(lines) and lines[i+1].strip() == '{':
                if i + 2 < len(lines) and 'DEBLOAT' in lines[i+2]:
                    break
                lines.insert(i + 2, '\treturn 0; /* DEBLOAT */\n')
                changes.append(f"{func_sig.split('(')[0].split()[-1]}() -> int no-op")
            break

# Handle start_amas_lib - it's declared extern, compiled from .o
# We need to find it differently
# Let's also search for any start_amas_lib definition
for i, line in enumerate(lines):
    if 'start_amas_lib' in line and 'void' in line and '{' not in line:
        # Could be a multi-line definition
        pass

with open(SERVICES, 'w') as f:
    f.writelines(lines)

# Also check usb.c for start_diskmon if not found in services.c
import os
USB_C = "/home/user/asuswrt/release/src/router/rc/usb.c"
if os.path.exists(USB_C):
    with open(USB_C, 'r') as f:
        ulines = f.readlines()

    for i, line in enumerate(ulines):
        if line.strip() == 'void start_diskmon(void)':
            if i + 1 < len(ulines) and ulines[i+1].strip() == '{':
                if i + 2 < len(ulines) and 'DEBLOAT' not in ulines[i+2]:
                    ulines.insert(i + 2, '\treturn; /* DEBLOAT */\n')
                    changes.append("usb.c: start_diskmon() -> void no-op")

    with open(USB_C, 'w') as f:
        f.writelines(ulines)

# Also handle the wps_pbcd start - it's in start_wps() which we don't
# want to fully disable, but we can make start_wps_pbcd() a no-op
# Check for it
for i, line in enumerate(lines):
    if 'start_wps_pbcd' in line and 'void' in line.lower():
        pass  # Will handle if found

print("=" * 60)
print("DEBLOAT V3 - REMAINING FUNCTIONS PATCHED")
print("=" * 60)
for c in changes:
    print(f"  [OK] {c}")
print(f"\nTotal: {len(changes)} additional patches")

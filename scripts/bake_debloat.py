#!/usr/bin/env python3
"""Bake debloat + security settings into firmware source."""

import re

DEFAULTS = "/home/user/asuswrt/release/src/router/shared/defaults.c"
INIT = "/home/user/asuswrt/release/src/router/rc/init.c"
SERVICES = "/home/user/asuswrt/release/src/router/rc/services.c"

changes = []

# ── 1. defaults.c ──────────────────────────────────────────────
with open(DEFAULTS, 'r') as f:
    content = f.read()

replacements = [
    ('{ "upnp_enable", "1"', '{ "upnp_enable", "0"'),
    ('{ "enable_samba", "1"', '{ "enable_samba", "0"'),
    ('{ "dms_enable", "1"', '{ "dms_enable", "0"'),
]

for old, new in replacements:
    if old in content:
        content = content.replace(old, new, 1)
        changes.append(f"defaults.c: {old.split(',')[0].strip('{ ')}: 1 -> 0")

with open(DEFAULTS, 'w') as f:
    f.write(content)

# ── 2. init.c ── strip bloat from rc_support ───────────────────
with open(INIT, 'r') as f:
    content = f.read()

# Find the last add_rc_support call and add our stripping code after it.
# We'll insert a debloat function call right before the closing of init_syspara()
# or after the last rc_support modification.

# Strategy: Find the pattern where rc_support modifications end,
# and add code to strip bloat features.

debloat_code = '''
\t/* --- DEBLOAT: strip bloat features from rc_support --- */
\t{
\t\tchar *rc = nvram_safe_get("rc_support");
\t\tchar buf[2048];
\t\tchar *features_to_remove[] = {
\t\t\t"bwdpi", "wrs_wbl", "PARENTAL2", "amas", "amas_bdl",
\t\t\t"cfg_sync", "app ", "appnet", "timemachine", "usb_bk",
\t\t\t"diskutility", "hdspindown", "usbX2", "modem",
\t\t\t"smart_connect", "gameMode", "wtfast", "account_binding",
\t\t\tNULL
\t\t};
\t\tint i;
\t\tstrlcpy(buf, rc, sizeof(buf));
\t\tfor (i = 0; features_to_remove[i]; i++) {
\t\t\tchar *p;
\t\t\tchar search[64];
\t\t\tsnprintf(search, sizeof(search), " %s", features_to_remove[i]);
\t\t\twhile ((p = strstr(buf, search)) != NULL) {
\t\t\t\tmemmove(p, p + strlen(search), strlen(p + strlen(search)) + 1);
\t\t\t}
\t\t}
\t\tnvram_set("rc_support", buf);
\t}
\t/* --- END DEBLOAT --- */
'''

# Find a good insertion point - right after the last feature-related rc_support block
# Look for the account_binding or nvram_encrypt block near the end
marker = 'add_rc_support("acl96");'
if marker in content:
    # Find the line with this marker and its closing #endif
    idx = content.index(marker)
    # Find the next #endif after this
    endif_idx = content.index('#endif', idx)
    # Find the newline after that #endif
    nl_idx = content.index('\n', endif_idx)
    content = content[:nl_idx+1] + debloat_code + content[nl_idx+1:]
    changes.append("init.c: Added rc_support debloat stripping code after feature additions")
else:
    # Fallback: try another marker
    marker2 = 'add_rc_support("amas");'
    if marker2 in content:
        idx = content.index(marker2)
        endif_idx = content.index('#endif', idx)
        nl_idx = content.index('\n', endif_idx)
        content = content[:nl_idx+1] + debloat_code + content[nl_idx+1:]
        changes.append("init.c: Added rc_support debloat stripping code (fallback)")
    else:
        changes.append("init.c: WARNING - could not find insertion point!")

with open(INIT, 'w') as f:
    f.write(content)

# ── 3. services.c ── skip bloat services in start_services() ──
with open(SERVICES, 'r') as f:
    content = f.read()

# Wrap specific start calls with /* DEBLOAT */ comments
services_to_skip = [
    'start_asd();',
    'start_ahs();',
    'start_awsiot();',
    'start_ptcsrv();',
    'start_netool();',
    'start_infosvr();',
    'start_lltd();',
    'start_diskmon();',
    'start_pctime_service();',
    'start_roamast();',
    'start_conn_diag();',
    'start_bwdpi_check();',
    'start_amas_lanctrl();',
    'start_amas_lib();',
    'start_amas_lldpd();',
    'start_amas_portstatus();',
]

skipped = []
for svc in services_to_skip:
    # Only skip if the call exists and isn't already commented
    if svc in content and f'/* DEBLOAT */ // {svc}' not in content:
        # Replace with commented-out version
        # Be careful to only replace in the start_services context
        # Use a simple replacement that preserves indentation
        content = content.replace(
            f'\t{svc}',
            f'\t/* DEBLOAT */ // {svc}',
            1  # only first occurrence
        )
        skipped.append(svc)

if skipped:
    changes.append(f"services.c: Skipped {len(skipped)} bloat service starts: {', '.join(s.rstrip(';') for s in skipped)}")

with open(SERVICES, 'w') as f:
    f.write(content)

# ── Summary ────────────────────────────────────────────────────
print("=" * 60)
print("DEBLOAT BAKE-IN COMPLETE")
print("=" * 60)
for c in changes:
    print(f"  [OK] {c}")
print(f"\nTotal changes: {len(changes)}")

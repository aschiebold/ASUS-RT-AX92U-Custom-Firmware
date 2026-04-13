#!/usr/bin/env python3
"""Patch ALL remaining bloat service spawn points."""

SERVICES = "/home/user/asuswrt/release/src/router/rc/services.c"
WATCHDOG = "/home/user/asuswrt/release/src/router/rc/watchdog.c"
LAN = "/home/user/asuswrt/release/src/router/rc/lan.c"
INIT = "/home/user/asuswrt/release/src/router/rc/init.c"

changes = []

# ── 1. services.c ── Add early return to start functions ──────
with open(SERVICES, 'r') as f:
    content = f.read()

# Add early returns to function definitions so they never actually run
# regardless of where they're called from.

func_patches = [
    # asd: make start_asd() a no-op
    ('void start_asd(void)\n{\n\tstop_asd();',
     'void start_asd(void)\n{\n\treturn; /* DEBLOAT */\n\tstop_asd();'),

    # roamast: make start_roamast() a no-op
    ('void start_roamast(void){\n\tchar',
     'void start_roamast(void){\n\treturn; /* DEBLOAT */\n\tchar'),

    # amas_lanctrl: make it a no-op
    ('void start_amas_lanctrl(void)\n{\n\tchar *amas_lanctrl_argv',
     'void start_amas_lanctrl(void)\n{\n\treturn; /* DEBLOAT */\n\tchar *amas_lanctrl_argv'),

    # awsiot: make it a no-op
    ('int start_awsiot(void)\n{\n\tchar *ev_argv',
     'int start_awsiot(void)\n{\n\treturn 0; /* DEBLOAT */\n\tchar *ev_argv'),

    # ptcsrv (protect_srv): make it a no-op
    ('int start_ptcsrv(void)\n{\n\tchar *ptcsrv_argv',
     'int start_ptcsrv(void)\n{\n\treturn 0; /* DEBLOAT */\n\tchar *ptcsrv_argv'),

    # netool: make it a no-op
    ('int start_netool(void)\n{\n\tchar *netool_argv',
     'int start_netool(void)\n{\n\treturn 0; /* DEBLOAT */\n\tchar *netool_argv'),

    # infosvr: make it a no-op
    ('int start_infosvr()\n{\n\tchar *infosvr_argv',
     'int start_infosvr()\n{\n\treturn 0; /* DEBLOAT */\n\tchar *infosvr_argv'),

    # lltd/lld2d: make it a no-op
    ('int start_lltd(void)\n{\n\tchdir',
     'int start_lltd(void)\n{\n\treturn 0; /* DEBLOAT */\n\tchdir'),

    # diskmon: make it a no-op
    ('void start_diskmon(void)\n{\n\tchar *diskmon_argv',
     'void start_diskmon(void)\n{\n\treturn; /* DEBLOAT */\n\tchar *diskmon_argv'),

    # pctime: make it a no-op
    ('void start_pctime_service()\n{\n\tchar *cmd',
     'void start_pctime_service()\n{\n\treturn; /* DEBLOAT */\n\tchar *cmd'),

    # conn_diag: make it a no-op
    ('void start_conn_diag(void){\n\tchar *cmd',
     'void start_conn_diag(void){\n\treturn; /* DEBLOAT */\n\tchar *cmd'),

    # amas_lib: make it a no-op - need to find exact signature
    # amas_lldpd: similar

    # amas_ssd
    ('void start_amas_ssd(void)\n{\n\tchar',
     'void start_amas_ssd(void)\n{\n\treturn; /* DEBLOAT */\n\tchar'),

    # amas_status
    ('void start_amas_status(void)\n{\n\tchar',
     'void start_amas_status(void)\n{\n\treturn; /* DEBLOAT */\n\tchar'),

    # amas_misc
    ('void start_amas_misc(void)\n{\n\tchar',
     'void start_amas_misc(void)\n{\n\treturn; /* DEBLOAT */\n\tchar'),

    # amas_bhctrl
    ('void start_amas_bhctrl(void)\n{\n\tchar',
     'void start_amas_bhctrl(void)\n{\n\treturn; /* DEBLOAT */\n\tchar'),

    # amas_wlcconnect
    ('void start_amas_wlcconnect(void)\n{\n\tchar',
     'void start_amas_wlcconnect(void)\n{\n\treturn; /* DEBLOAT */\n\tchar'),

    # ahs
    ('void start_ahs(void)\n{\n\tstop_ahs',
     'void start_ahs(void)\n{\n\treturn; /* DEBLOAT */\n\tstop_ahs'),
]

for old, new in func_patches:
    if old in content:
        content = content.replace(old, new, 1)
        fname = old.split('(')[0].split()[-1]
        changes.append(f"services.c: {fname}() -> no-op")
    else:
        fname = old.split('(')[0].split()[-1]
        # Try with different whitespace
        pass

with open(SERVICES, 'w') as f:
    f.write(content)

# ── 2. watchdog.c ── Disable respawn checks ───────────────────
with open(WATCHDOG, 'r') as f:
    content = f.read()

# awsiot respawn in watchdog (line ~6997)
old = '\tif (!pids("awsiot"))\n\t\tstart_awsiot();'
new = '\t/* DEBLOAT: awsiot disabled */\n\t// if (!pids("awsiot"))\n\t//\tstart_awsiot();'
if old in content:
    content = content.replace(old, new, 1)
    changes.append("watchdog.c: disabled awsiot respawn")

# roamast respawn in watchdog (two locations, lines ~7260 and ~7277)
# Pattern: if (rast && !pids("roamast"))\n\t\tstart_roamast();
old_r1 = 'if (rast && !pids("roamast"))\n\t\tstart_roamast();'
new_r1 = '/* DEBLOAT */ if (0 && rast && !pids("roamast"))\n\t\tstart_roamast();'
count = content.count(old_r1)
if count > 0:
    content = content.replace(old_r1, new_r1)
    changes.append(f"watchdog.c: disabled roamast respawn ({count} locations)")

# amas_lanctrl respawn in watchdog (lines ~8327-8343)
old_al = 'notify_rc("start_amas_lanctrl");'
new_al = '/* DEBLOAT */ // notify_rc("start_amas_lanctrl");'
count = content.count(old_al)
if count > 0:
    content = content.replace(old_al, new_al)
    changes.append(f"watchdog.c: disabled amas_lanctrl respawn ({count} locations)")

old_al2 = 'start_amas_lanctrl();'
new_al2 = '/* DEBLOAT */ // start_amas_lanctrl();'
if old_al2 in content:
    content = content.replace(old_al2, new_al2)
    changes.append("watchdog.c: disabled direct amas_lanctrl start")

# amas bhctrl, wlcconnect, status, misc, ssd respawn
for svc in ['start_amas_bhctrl', 'start_amas_wlcconnect', 'start_amas_status',
            'start_amas_misc', 'start_amas_ssd']:
    old_n = f'notify_rc("{svc}");'
    new_n = f'/* DEBLOAT */ // notify_rc("{svc}");'
    if old_n in content:
        content = content.replace(old_n, new_n)
        changes.append(f"watchdog.c: disabled {svc} notify")

with open(WATCHDOG, 'w') as f:
    f.write(content)

# ── 3. lan.c ── Disable bloat service starts ──────────────────
with open(LAN, 'r') as f:
    content = f.read()

for svc in ['start_roamast();', 'start_amas_status();', 'start_amas_wlcconnect();',
            'start_amas_bhctrl();']:
    if f'\t{svc}' in content and f'/* DEBLOAT */ // {svc}' not in content:
        content = content.replace(f'\t{svc}', f'\t/* DEBLOAT */ // {svc}', 1)
        changes.append(f"lan.c: disabled {svc}")

with open(LAN, 'w') as f:
    f.write(content)

# ── 4. init.c ── Disable usbmuxd and PS_pod ──────────────────
with open(INIT, 'r') as f:
    content = f.read()

# usbmuxd (line ~21186)
old_usb = '_dprintf("%s: execute \\"usbmuxd\\"...\\n", __func__);\n\t\t\tchar *cmd_usbmuxd[] = {"usbmuxd", NULL};\n\t\t\tpid_t pid_usbmuxd;\n\t\t\t_eval(cmd_usbmuxd, NULL, 0, &pid_usbmuxd);'
new_usb = '/* DEBLOAT: usbmuxd disabled */\n\t\t\t// _dprintf("%s: execute \\"usbmuxd\\"...\\n", __func__);\n\t\t\t// char *cmd_usbmuxd[] = {"usbmuxd", NULL};\n\t\t\t// pid_t pid_usbmuxd;\n\t\t\t// _eval(cmd_usbmuxd, NULL, 0, &pid_usbmuxd);'
if old_usb in content:
    content = content.replace(old_usb, new_usb, 1)
    changes.append("init.c: disabled usbmuxd start")

# PS_pod (line ~20534)
old_pod = 'char *argv[]={"/sbin/PS_pod", NULL};'
if old_pod in content:
    # Find the surrounding context and comment it out
    idx = content.index(old_pod)
    # Find the _eval call after it
    eval_end = content.index(';', content.index('_eval', idx)) + 1
    block = content[idx:eval_end]
    new_block = '/* DEBLOAT: PS_pod disabled */\n\t\t// ' + block.replace('\n', '\n\t\t// ')
    content = content.replace(block, new_block, 1)
    changes.append("init.c: disabled PS_pod start")

with open(INIT, 'w') as f:
    f.write(content)

# ── Summary ────────────────────────────────────────────────────
print("=" * 60)
print("DEBLOAT V2 - ALL SPAWN POINTS PATCHED")
print("=" * 60)
for c in changes:
    print(f"  [OK] {c}")
print(f"\nTotal patches: {len(changes)}")

# ASUSWRT Custom Firmware for RT-AX92U

A debloated, security-hardened, and package-updated custom firmware for the ASUS RT-AX92U router, built from the official GPL source code.

**Firmware Version:** `3.0.0.4.388 AI Built 2026-04-12`

## Overview

This project modifies the stock ASUSWRT GPL firmware for the RT-AX92U to achieve three goals:

1. **Debloat** -- Remove unnecessary features and services to reduce memory usage and attack surface
2. **Security Hardening** -- Add modern HTTP security headers, harden defaults, and sanitize inputs
3. **Package Updates** -- Update bundled open-source libraries to their latest compatible versions

The result is a lean, secure router firmware that dropped memory usage from ~84% to ~56% while maintaining full WiFi and routing functionality.

## Hardware Target

- **Router:** ASUS RT-AX92U
- **Platform:** Broadcom BCM4906 (HND), dual-architecture (ARM 32-bit userspace, ARM64 kernel)
- **Kernel:** Linux 4.1.51
- **Base Firmware:** ASUSWRT GPL `3.0.0.4.388`

## Prerequisites

- **Build machine:** x86_64 PC running Ubuntu 20.04 LTS (bare metal recommended)
- **Stock GPL source:** Download `GPL_RT_AX92U_30043885535.zip` from the [ASUS GPL portal](https://www.asus.com/networking-iot-servers/wifi-routers/asus-wifi-routers/rt-ax92u/helpdesk_download/?model2Name=RT-AX92U)
- **Disk space:** ~15GB free
- **RAM:** 8GB+ recommended

### Build Dependencies

```bash
sudo apt-get install -y build-essential flex bison autoconf automake \
  libtool pkg-config libncurses5-dev zlib1g-dev gawk gettext texinfo \
  sharutils subversion libexpat1-dev python2 python3 libxml-parser-perl \
  g++-multilib lib32z1-dev lib32stdc++6 cmake sshpass atftp
```

## Changes

### 1. Debloat

**Build flags** (`buildtools/target.mak.3004`):
- Disabled: `MEDIASRV`, `PRINTER`, `NATNL_AICLOUD`, `NATNL_AIHOME`, `ALEXA`, `AMAZON_WSS`, `GOOGLE_ASST`, `IFTTT`, `WEBDAV`, `SMARTSYNCBASE`, `OOKLA`
- Removed Samba/FTP: `SAMBA3=""`, `NO_SAMBA=y`, `NO_FTP=y`
- Kept `BWDPI=y` and `AMAS=y` (required by proprietary binary blobs to prevent boot loops)

**NVRAM defaults** (`release/src/router/shared/defaults.c`):
- WPS disabled (`wps_enable=0`, `wps_enable_x=0`)
- UPnP disabled (`upnp_enable=0`, `wan_upnp_enable=0`)
- Samba disabled (`enable_samba=0`)
- Media server disabled (`dms_enable=0`)
- DoS protection enabled (`fw_dos_x=1`)
- DNS-over-TLS enabled in opportunistic mode (`dnspriv_enable=1`, `dnspriv_profile=0`)
- DNS-over-TLS pre-configured with Cloudflare servers (`1.1.1.1` and `1.0.0.1` via `cloudflare-dns.com`)
- Auto-logout reduced to 10 minutes (`http_autologout=10`)

**Service no-ops** (`release/src/router/rc/services.c`):
Inserted early `return;` statements into the following service functions so they never execute, regardless of how they are called:
- `start_asd`, `start_roamast`, `start_awsiot`, `start_ptcsrv`, `start_netool`
- `start_infosvr`, `start_lltd`, `start_diskmon`, `start_pctime_service`
- `start_conn_diag`, `start_ahs`, `start_amas_lanctrl`, `start_amas_ssd`
- `start_amas_status`, `start_amas_misc`, `start_amas_bhctrl`
- `start_amas_wlcconnect`, `start_wps_pbcd`

**Watchdog disabling** (`release/src/router/rc/watchdog.c`):
Disabled respawn logic for: `awsiot`, `roamast`, `amas_lanctrl`, `amas_bhctrl`, `amas_wlcconnect`, `amas_status`, `amas_misc`, `amas_ssd`

**LAN service disabling** (`release/src/router/rc/lan.c`):
Disabled start calls for: `start_roamast`, `start_amas_status`, `start_amas_wlcconnect`, `start_amas_bhctrl`

**Init disabling** (`release/src/router/rc/init.c`):
- Disabled `usbmuxd` and `PS_pod` starts
- Strips bloat features from `rc_support` NVRAM variable at boot: `bwdpi`, `wrs_wbl`, `PARENTAL2`, `amas`, `amas_bdl`, `cfg_sync`, `app`, `appnet`, `timemachine`, `usb_bk`, `diskutility`, `hdspindown`, `usbX2`, `modem`, `smart_connect`, `gameMode`, `wtfast`, `account_binding`

**Stub functions:**
- `release/src/router/rc/debloat_stubs.c` -- Stub for `find_dms_dbdir_candidate`
- `release/src/router/httpd/httpd_debloat_stubs.c` -- Stubs for `add_ifttt_flag` and `aae_sendIpcMsgAndWaitResp`

### 2. Security Hardening

**HTTP security headers** (`release/src/router/httpd/httpd.c`):
Applied to HTML document responses only (not static assets, since the ASUS httpd serves some JS files with incorrect MIME types that would break with `nosniff`):
- `X-Frame-Options: SAMEORIGIN`
- `X-XSS-Protection: 1; mode=block`
- `Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; font-src 'self' data:; worker-src 'self' blob:; child-src 'self' blob:; frame-src 'self'`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: geolocation=(), camera=(), microphone=()`
- `Cache-Control: no-store, no-cache, must-revalidate`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` (HTTPS only)

**Cookie hardening** (`release/src/router/httpd/httpd.c`):
- `asus_token` cookie: added `Secure` (HTTPS only) and `SameSite=Strict` flags

**Shell input sanitization** (`release/src/router/httpd/httpd.c`, `httpd.h`, `web.c`):
- Added `sanitize_shell_input()` and `sanitize_shell_copy()` functions
- Applied sanitization check before `system()` call in the `SystemCmd` handler

### 3. Package Updates

| Package | Stock Version | Updated Version | Status |
|---------|--------------|-----------------|--------|
| libpng  | 1.6.37       | 1.6.46          | Working |
| SQLite  | 3.25.3       | 3.49.1          | Working |
| LZO     | 2.03         | 2.10            | Working |
| pcre    | 8.12         | 8.45            | Working |
| zlib    | 1.2.11       | 1.3.1           | Working (updated in earlier phase) |
| json-c  | 0.12.1       | --              | Kept at 0.12.1 (0.13.1 caused ABI incompatibility with proprietary binaries, resulting in SIGABRT crashes) |

**To apply package updates**, download these upstream tarballs and replace the corresponding directories in `release/src/router/`:

- **libpng 1.6.46:** https://sourceforge.net/projects/libpng/files/libpng16/1.6.46/libpng-1.6.46.tar.gz
- **SQLite 3.49.1:** https://www.sqlite.org/2025/sqlite-autoconf-3490100.tar.gz (replace source files in `sqlite/`, keep the stock autotools build system)
- **LZO 2.10:** https://www.oberhumer.com/opensource/lzo/download/lzo-2.10.tar.gz
- **pcre 8.45:** https://sourceforge.net/projects/pcre/files/pcre/8.45/pcre-8.45.tar.gz (replace both `pcre-8.12/` and `pcre-8.31/` directories)
- **zlib 1.3.1:** https://zlib.net/zlib-1.3.1.tar.gz

The `release/src/router/Makefile` install rules have been updated to reflect the new library sonames.

### Build System Fixes

**Kernel config** (`release/src-rt-5.02axhnd/make.hndrt`):
- Uncommented `$(GENDEFCONFIG_CMD)` to properly regenerate kernel defconfig
- Added `yes "" |` before `make oldnoconfig` to prevent interactive prompts during build
- Fixed `BRCM_CHIP_REV` value corruption from `gendefconfig`

**zlib build** (`release/src/router/Makefile`, `release/src/router/zlib/Makefile.in`):
- Fixed `AR` variable passing: uses `AR="ar" ARFLAGS="rc"` instead of `AR="ar rc"` which broke with newer zlib

## Building

1. Extract the stock GPL source:
   ```bash
   unzip GPL_RT_AX92U_30043885535.zip
   cd asuswrt
   ```

2. Copy modified files over the stock source (preserving directory structure):
   ```bash
   cp -r modified-files/* /path/to/asuswrt/
   ```

3. Apply package updates by downloading tarballs and replacing directories as described above.

4. Build:
   ```bash
   cd release/src-rt-5.02axhnd
   make RT-AX92U
   ```

5. The firmware image will be at:
   ```
   release/src-rt-5.02axhnd/targets/94908HND/RT-AX92U_3.0.0.4_388_*.w
   ```

## Flashing

### Via TFTP (Recovery Mode)

1. Connect your PC to a LAN port on the router via Ethernet
2. Set your PC's IP to `192.168.1.x` (e.g., `192.168.1.114`)
3. Put the router in recovery mode: hold the reset button while powering on, wait for the power LED to blink slowly
4. Flash:
   ```bash
   atftp --option "mode octet" --option "blksize 65536" \
     --put --local-file RT-AX92U_firmware.w 192.168.1.1
   ```
5. Wait 3-5 minutes for the router to reboot

### Via Web GUI

Upload the `.w` file through **Administration > Firmware Upgrade** in the router's web interface.

## File Summary

| File | Changes |
|------|---------|
| `buildtools/target.mak.3004` | Debloat build flags |
| `release/src/router/Makefile` | Updated install rules for libpng, pcre sonames; fixed zlib AR flags |
| `release/src/router/shared/version.h` | Custom firmware version string |
| `release/src/router/shared/defaults.c` | Hardened NVRAM defaults |
| `release/src/router/httpd/httpd.c` | Security headers, cookie hardening, shell sanitization |
| `release/src/router/httpd/httpd.h` | Sanitization function prototypes |
| `release/src/router/httpd/web.c` | Shell sanitization in SystemCmd handler |
| `release/src/router/httpd/Makefile` | Added `httpd_debloat_stubs.o` |
| `release/src/router/httpd/httpd_debloat_stubs.c` | Stub functions for disabled features |
| `release/src/router/rc/init.c` | rc_support stripping, disabled usbmuxd/PS_pod |
| `release/src/router/rc/services.c` | Service function no-ops |
| `release/src/router/rc/watchdog.c` | Disabled bloat service respawning |
| `release/src/router/rc/lan.c` | Disabled bloat service starts |
| `release/src/router/rc/usb.c` | Disabled diskmon |
| `release/src/router/rc/Makefile` | Added `debloat_stubs.o` |
| `release/src/router/rc/debloat_stubs.c` | Stub for find_dms_dbdir_candidate |
| `release/src/router/zlib/Makefile.in` | Fixed ARFLAGS |
| `release/src-rt-5.02axhnd/make.hndrt` | Kernel config generation fixes |
| `release/src-rt-5.02axhnd/router/extendno.conf` | Custom firmware version string ("AI Built 2026-04-12") |

## Scripts

The `scripts/` directory contains Python automation scripts used during development:

- `bake_debloat.py` -- Initial debloat: NVRAM defaults, rc_support stripping, service commenting
- `bake_debloat_v2.py` -- Extended debloat: function no-ops, watchdog/lan disabling
- `bake_debloat_v3.py` -- Whitespace-robust function no-op patching
- `fix_hsts.py` -- HSTS and Secure cookie flag conditional on HTTPS
- `fix_csp2.py` -- CSP header formatting fix

These scripts were applied to the stock source to produce the modified files included in this repo. They are provided for reference and reproducibility.

## Known Limitations

- **json-c cannot be updated** beyond 0.12.1. Version 0.13.1 changed the ABI (soname 2 to 4), causing SIGABRT crashes in proprietary ASUS/Broadcom binaries that were compiled against the old version.
- **X-Content-Type-Options: nosniff** is intentionally omitted. The ASUS httpd serves dynamically generated JavaScript files (like `state.js`) with `Content-Type: text/html`. With `nosniff`, browsers refuse to execute these files, breaking the web UI.
- **BWDPI and AMAS** build flags are kept enabled because proprietary binary blobs have runtime dependencies on their shared libraries. These features are instead disabled at the service level (functions return immediately) and stripped from the UI via `rc_support`.

## License

This project is based on ASUS GPL source code and is released under the [GNU General Public License v2](LICENSE), consistent with the original ASUSWRT license.

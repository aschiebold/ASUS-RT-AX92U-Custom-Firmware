#!/usr/bin/env python3
"""Fix HSTS and Secure cookie to only apply over HTTPS."""

HTTPD = "/home/user/asuswrt/release/src/router/httpd/httpd.c"

with open(HTTPD, 'r') as f:
    content = f.read()

# 1. Wrap HSTS in send_headers with do_ssl check
old_hsts1 = '    (void) fprintf( conn_fp, "Strict-Transport-Security: max-age=31536000; includeSubDomains\\r\\n");'
new_hsts1 = '    if (do_ssl) (void) fprintf( conn_fp, "Strict-Transport-Security: max-age=31536000; includeSubDomains\\r\\n");'

count = content.count(old_hsts1)
if count == 2:
    content = content.replace(old_hsts1, new_hsts1)
    print(f"[OK] Wrapped {count} HSTS lines with do_ssl check")
else:
    print(f"[WARN] Expected 2 HSTS lines, found {count}")

# 2. Fix Secure cookie flag - only add Secure when do_ssl
old_cookie = '\t(void) fprintf( conn_fp, "Set-Cookie: asus_token=%s; HttpOnly; Secure; SameSite=Strict\\r\\n",asus_token );'
new_cookie = '\tif (do_ssl)\n\t\t(void) fprintf( conn_fp, "Set-Cookie: asus_token=%s; HttpOnly; Secure; SameSite=Strict\\r\\n",asus_token );\n\telse\n\t\t(void) fprintf( conn_fp, "Set-Cookie: asus_token=%s; HttpOnly; SameSite=Strict\\r\\n",asus_token );'

if old_cookie in content:
    content = content.replace(old_cookie, new_cookie)
    print("[OK] Cookie Secure flag now conditional on do_ssl")
else:
    print("[WARN] Could not find cookie line")

with open(HTTPD, 'w') as f:
    f.write(content)

print("[OK] httpd.c written")
print("\n=== HSTS/Cookie fix complete ===")

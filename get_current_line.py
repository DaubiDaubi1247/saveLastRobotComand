#!/usr/bin/env python3
"""Query KRC4 (KUKAVARPROXY) for the currently executing program line.

This tool attempts a set of likely variable names via the same
`Var_ShowVar` JSON-RPC used in `previous.py`. If none of the
candidates return a useful value, the script prints suggestions
for a small KRL change (exposing a variable) to report the current
line from the robot program.
"""
import argparse
import json
import socket
import sys
import time
import re

def request(command, client, timeout=3):
    if not command.endswith('\n'):
        command += '\n'
    client.send(command.encode())
    resp = b''
    client.settimeout(timeout)
    while True:
        chunk = client.recv(4096)
        if not chunk:
            break
        resp += chunk
        if resp.endswith(b'\n'):
            break
    try:
        return json.loads(resp)
    except Exception:
        return resp.decode('utf-8', errors='ignore')

def try_vars(addr, port, vars_list, timeout=3):
    # legacy: keep function for compatibility, but prefer explicit queries
    client = socket.socket()
    client.settimeout(timeout)
    client.connect((addr, port))
    for v in vars_list:
        msg = "{'method':'Var_ShowVar','params':['%s'],'id':1}\n" % v
        try:
            r = request(msg, client, timeout)
        except Exception as e:
            client.close()
            raise
        if isinstance(r, (list, dict)):
            sval = json.dumps(r, ensure_ascii=False)
        else:
            sval = str(r)
        sval = sval.strip()
        if not sval or sval in ('[]', "''"):
            continue
        # return first non-empty response as fallback
        client.close()
        return v, sval, sval
    client.close()
    return None, None, None

def get_program_and_line(addr, port, timeout=3):
    def get_var(var):
        client = socket.socket()
        client.settimeout(timeout)
        client.connect((addr, port))
        msg = "{'method':'Var_ShowVar','params':['%s'],'id':1}\n" % var
        try:
            r = request(msg, client, timeout)
        finally:
            try:
                client.close()
            except Exception:
                pass
        if isinstance(r, (list, dict)):
            sval = json.dumps(r, ensure_ascii=False)
        else:
            sval = str(r)
        return sval.strip()

    prog = get_var('$PRO_NAME[]')
    line_raw = get_var('$LINE')
    # try parse line to int
    line = None
    if line_raw:
        m = re.search(r'(\d+)', line_raw)
        if m:
            try:
                line = int(m.group(1))
            except Exception:
                line = None
    return prog or None, line, line_raw or None

def main():
    p = argparse.ArgumentParser(description='Get current executing line from KRC4 via KUKAVARPROXY')
    p.add_argument('--host', required=True, help='Robot IP address')
    p.add_argument('--port', type=int, default=3333, help='KUKAVARPROXY port (default 3333)')
    p.add_argument('--vars', help='Comma-separated extra variable names to try')
    args = p.parse_args()

    # Directly query program name and line
    try:
        prog, line, line_raw = get_program_and_line(args.host, args.port)
    except Exception as e:
        print('ERROR: communication failed:', e, file=sys.stderr)
        sys.exit(2)

    if prog is None and line is None:
        print('Could not read $PRO_NAME[] or $LINE from robot.')
        print('If direct access is not available, expose a variable from KRL as fallback:')
        print('\nExample KRL snippet (add to your program):')
        print('  GLOBAL INT CURRENT_LINE')
        print('  CURRENT_LINE = $LINE')
        print('\nThen read `CURRENT_LINE` via KUKAVARPROXY.')
        sys.exit(1)

    out = {'program': prog, 'line': line, 'line_raw': line_raw}
    print(json.dumps(out, ensure_ascii=False))

if __name__ == '__main__':
    main()

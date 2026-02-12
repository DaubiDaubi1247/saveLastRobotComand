#!/usr/bin/env python3
import argparse
import json
import socket
import sys

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

def get_program_and_line(addr, port, timeout=3):
    """Return program name read from $PRO_IP (string or None)."""
    client = socket.socket()
    client.settimeout(timeout)
    client.connect((addr, port))
    msg = "{'method':'Var_ShowVar','params':['$PRO_IP'],'id':1}\n"
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
    sval = sval.strip()
    return sval or None

def main():
    p = argparse.ArgumentParser(description='Get current executing program name from KRC4 via KUKAVARPROXY')
    p.add_argument('--host', default="192.168.6.139", help='Robot IP address')
    p.add_argument('--port', type=int, default=3333, help='KUKAVARPROXY port (default 3333)')
    args = p.parse_args()

    try:
        prog = get_program_and_line(args.host, args.port)
    except Exception as e:
        print('ERROR: communication failed:', e, file=sys.stderr)
        sys.exit(2)

    if prog is None:
        print('Could not read $PRO_IP from robot.')
        sys.exit(1)

    print(prog)

if __name__ == '__main__':
    main()
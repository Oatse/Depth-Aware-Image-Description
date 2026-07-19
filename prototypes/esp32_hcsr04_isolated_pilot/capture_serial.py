from __future__ import annotations

import argparse
import time

import serial


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", required=True)
    parser.add_argument("--seconds", type=float, default=15.0)
    args = parser.parse_args()

    deadline = time.monotonic() + args.seconds
    received = 0

    with serial.Serial(args.port, 115200, timeout=0.5) as connection:
        connection.dtr = False
        connection.rts = True
        time.sleep(0.1)
        connection.rts = False
        time.sleep(0.3)
        connection.reset_input_buffer()
        while time.monotonic() < deadline:
            raw_line = connection.readline()
            if not raw_line:
                continue
            print(raw_line.decode("utf-8", errors="replace").strip(), flush=True)
            received += 1

    if received == 0:
        print("ERROR: no serial output received")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

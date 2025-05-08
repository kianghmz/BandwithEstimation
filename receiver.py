import socket
import struct
import time
import pandas as pd
import os

PORT = 6000
HEADER_STRUCT = struct.Struct("!IIIQ")
BUFFER_SIZE = 2048
OUTPUT_FILE = "receiver_log.xlsx"

if os.path.exists(OUTPUT_FILE):
    df = pd.read_excel(OUTPUT_FILE)
else:
    df = pd.DataFrame(columns=["run_id", "group_id", "packet_id", "packet_size", "send_time_ns", "receive_time_ns"])

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", PORT))
sock.settimeout(0.1)

print(f"Receiver listening on port {PORT}...")
last_receive_time = time.time()
INACTIVITY_TIMEOUT = 10

try:
    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            now = time.time()
            receive_time_ns = time.time_ns()
            last_receive_time = now

            if len(data) < HEADER_STRUCT.size:
                continue

            run_id, group_id, packet_id, send_time_ns = HEADER_STRUCT.unpack(data[:HEADER_STRUCT.size])
            packet_size = len(data)

            df.loc[len(df)] = [run_id, group_id, packet_id, packet_size, send_time_ns, receive_time_ns]
            print(f"Received: run={run_id}, group={group_id}, id={packet_id}, size={packet_size}")

        except socket.timeout:
            if time.time() - last_receive_time > INACTIVITY_TIMEOUT:
                print("No packet for 10s, waiting for next run...")
                last_receive_time = time.time()

except KeyboardInterrupt:
    print("Saving to Excel...")
    df.to_excel(OUTPUT_FILE, index=False)
    print("All data saved.")

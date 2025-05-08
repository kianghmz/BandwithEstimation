import socket
import struct
import time
import pandas as pd

DEST_IP = "192.168.56.130"
DEST_PORT = 6000
RUN_ID = 1
GROUP_COUNT = 3
INTER_GROUP_DELAY = 0.5
INTER_PACKET_DELAY = 0.0005

REFERENCE_SIZE = 100
OTHER_SIZES = sorted([1493, 1363, 1444, 1332, 1465, 1424, 1390])
HEADER_STRUCT = struct.Struct("!IIIQ")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
log_data = []

for group_id in range(GROUP_COUNT):
    send_time_ns = time.time_ns()
    header = HEADER_STRUCT.pack(RUN_ID, group_id, 0, send_time_ns)
    payload = bytes(REFERENCE_SIZE - HEADER_STRUCT.size)
    sock.sendto(header + payload, (DEST_IP, DEST_PORT))
    log_data.append([RUN_ID, group_id, 0, REFERENCE_SIZE, send_time_ns])
    time.sleep(INTER_PACKET_DELAY)

    for packet_id, size in enumerate(OTHER_SIZES, start=1):
        send_time_ns = time.time_ns()
        header = HEADER_STRUCT.pack(RUN_ID, group_id, packet_id, send_time_ns)
        payload = bytes(size - HEADER_STRUCT.size)
        sock.sendto(header + payload, (DEST_IP, DEST_PORT))
        log_data.append([RUN_ID, group_id, packet_id, size, send_time_ns])
        time.sleep(INTER_PACKET_DELAY)

    time.sleep(INTER_GROUP_DELAY)

sock.close()
df = pd.DataFrame(log_data, columns=["run_id", "group_id", "packet_id", "packet_size", "send_time_ns"])
df.to_excel("sender_log.xlsx", index=False)
print("Sender finished and sender_log.xlsx saved.")

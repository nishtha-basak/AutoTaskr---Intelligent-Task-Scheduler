import socket
import threading
import time
import json
import logging
from log_config import *

def handle_client(conn, addr):
    logging.info(f"[Worker] Connected by {addr}")
    data = conn.recv(1024)
    if data:
        task = json.loads(data.decode())
        logging.info(f"[Worker] Executing task: {task['title']}")
        time.sleep(task['duration'] * 2)  # Simulate execution time
        conn.sendall(b"done")
    conn.close()

def start_worker_server(host='localhost', port=6000):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen()
    logging.info(f"[Worker] Listening on {host}:{port}")
    print(f"[Worker] Listening on {host}:{port}")  # Optional visible confirmation
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start_worker_server()

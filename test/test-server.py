"""
Server for local tests
Loads dataset of beacon positions, waits for data and calculates position
"""
import logging
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import server as s

import time
import numpy as np
from scipy.optimize import least_squares

import pandas as pd

import asyncio

# Using websocket for testing because is easier, actual comms should use something else
from websockets.asyncio.server import serve

class beaconManagerWS(s.beaconManager):
    async def beacon_data_receiver(self, websocket):
        """
        Expected messsage format: beacon_id@beacon_distance
        """
        async for message in websocket:
            log.debug(f"Message received: {message}")
            message = message.split("@")

            try:
                float(message[1])

            except ValueError:
                log.warning("Invalid message format - distance provided is NOT a float")

            except IndexError:
                log.warning("Invalid message format")

            else:
                self.update_beacon_distance(int(message[0]), float(message[1]))

async def main():
    base_time = time.time()

    log.debug("Loading config dataset 1")

    try:
        beacon_manager = beaconManagerWS("./datasets/beacon-config-dataset-1.csv")

    except FileNotFoundError:
        log.critical(f'Error loading beacon config 1 - File not found{s.dt(base_time)}')
        raise

    log.info(f"Beacon config 1 loaded{s.dt(base_time)}")

    base_time = time.time()

    ws_server = await serve(beacon_manager.beacon_data_receiver, "localhost", 8765)
    server_task = asyncio.create_task(ws_server.wait_closed())

    log.info(f"Server online, waiting for packets...{s.dt(base_time)}")

    while True:
        await asyncio.sleep(5)
        beacon_manager.calculate_position()

if __name__ == '__main__':
    start_time = time.time()

    start_datetime = time.strftime("%Y-%m-%d %H %M %S")

    file_handler = logging.FileHandler(f"./logs/test-server {start_datetime}.log", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(s.log_format))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(s.ColoredFormatter(s.log_format))

    log = logging.getLogger("Logger")
    log.setLevel(logging.DEBUG)
    log.addHandler(file_handler)
    log.addHandler(console_handler)

    log.debug(f"Start datetime: {start_datetime}")

    #TODO: Graceful termination
    try:
        asyncio.run(main())
    except:
        log.critical(f"Program interrupted - Runtime: {s.runtime(start_time)}")
        raise
"""
Server for local tests
Loads dataset of beacon positions, waits for data and calculates position
"""
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

# ANSI color escape sequences for color printing
class ts:
    HEADER = '\033[48;2;0;68;102m\033[38;2;255;255;255m'
    OK = '\033[38;2;0;114;178m'
    WARNING = '\033[38;2;230;159;0m'
    FAIL = '\033[38;2;213;94;0m'
    OBSERVATION = '\033[38;2;153;153;153m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    ENDC = '\033[0m'

class beaconManagerWS(s.beaconManager):
    async def beacon_data_receiver(self, websocket):
        """
        Expected messsage format: beacon_id@beacon_distance
        """
        async for message in websocket:
            print(f"\n{ts.OBSERVATION}Message received: {message}{ts.ENDC}")
            message = message.split("@")

            try:
                float(message[1])

            except ValueError:
                print(f"{ts.WARNING}Invalid message format - distance provided is NOT a float{ts.ENDC}\n")

            except IndexError:
                print(f"{ts.WARNING}Invalid message format{ts.ENDC}\n")

            else:
                self.update_beacon_distance(message[0], int(message[1]))

async def main():
    base_time = time.time()

    print(time.strftime("%H:%M:%S %d/%m/%Y"))
    print(f"{ts.HEADER}Loading config dataset 1{ts.ENDC}")

    try:
        beacon_manager = beaconManagerWS("./datasets/beacon-config-dataset-1.csv")

    except FileNotFoundError:
        print(f'\n{ts.FAIL}Error loading beacon config 1 - File not found{s.dt(base_time)}{ts.ENDC}')
        raise

    print(f"{ts.OK}Beacon config 1 loaded{s.dt(base_time)}{ts.ENDC}")

    base_time = time.time()

    ws_server = await serve(beacon_manager.beacon_data_receiver, "localhost", 8765)
    server_task = asyncio.create_task(ws_server.wait_closed())

    print(f"{ts.OK}Server online, waiting for packets...{s.dt(base_time)}{ts.ENDC}")

    while True:
        await asyncio.sleep(5)
        beacon_manager.calculate_position()

if __name__ == '__main__':
    start_time = time.time()

    #TODO: Graceful termination
    try:
        asyncio.run(main())
    except:
        print(f"\n{ts.WARNING}Program interrupted - Runtime: {s.runtime(start_time)}{ts.ENDC}\n")
"""Fake transmitter, loads dataset and sends"""

import csv

import asyncio
from websockets.asyncio.client import connect

import numpy as np
from scipy.optimize import least_squares


async def send_data(data, rate):
    async with connect("ws://localhost:8765") as websocket:

        await websocket.send("Hello world!")
        message = await websocket.recv()
        print(message)

async def hello():
    async with connect("ws://localhost:8765") as websocket:
        await websocket.send("Hello world!")
        message = await websocket.recv()
        print(message)


if __name__ == "__main__":
    asyncio.run(hello())
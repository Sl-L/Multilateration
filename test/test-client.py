"""Fake transmitter, loads dataset and sends"""

import csv

import asyncio
from websockets.asyncio.client import connect

import pandas as pd

async def send_data(dataset: str):
    data = pd.read_csv(dataset)

    for index, row in data.iterrows():
        message = f"{int(row['beacon_id'])}@{row['distance']:.4f}"
        async with connect("ws://localhost:8765") as websocket:
            await websocket.send(message)

if __name__ == "__main__":
    asyncio.run(send_data("./datasets/beacon-distance-dataset-1.csv"))
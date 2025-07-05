import time
import numpy as np
from scipy.optimize import least_squares

import pandas as pd

import asyncio

import sys
import logging
log = logging.getLogger(__name__)

import argparse

"""
TODO: Implement comms with beacons
"""

# ANSI color escape sequences for color printing
RESET = "\033[0m"
COLORS = {
    logging.DEBUG: "\033[36m",
    logging.INFO: "\033[38;2;153;153;153m",
    logging.WARNING: "\033[38;2;230;159;0m",
    logging.ERROR: "\033[38;2;213;94;0m",
    logging.CRITICAL: "\033[1;41m",
}

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        color = COLORS.get(record.levelno, RESET)
        message = super().format(record)
        return f"{color}{message}{RESET}"

log_format = "%(asctime)s [%(levelname)s] %(message)s"

def dt(base_time: float) -> str:
    """
    Milliseconds passed since base_time with 2 decimals
    """
    return f'\t({(1000*(time.time() - base_time)):.2f} ms)'

def runtime(start_time: float) -> str:
    """
    Seconds passed since start_time
    """
    return f'({((time.time() - start_time)):.2f} s)'

class beaconManager:
    def __init__(self, dataset: str):
        beacons = pd.read_csv(dataset)
        self.beacons_pos_array = beacons[['pos_x', 'pos_y']].to_numpy()
        self.beacons_dict = dict.fromkeys(beacons['beacon_id'], None)
        self.log = logging.getLogger("Logger")

    def update_beacon_distance(self, id, distance) -> None:
        self.log.debug("Updating beacon distance")
        if id in self.beacons_dict:
            self.beacons_dict[id] = distance
        
        else:
            self.log.warning(f"Beacon ( id: {id} type: {type(id)} ) not on list {str(self.beacons_dict.keys())} - Ignoring data")

    def residuals(self, p, beacons, distances) -> np.ndarray:
        x, y = p
        return np.sqrt((x - beacons[:, 0])**2 + (y - beacons[:, 1])**2) - distances
    
    def triangulate(self) -> list[float, float]:
        """
        Find power center, used to get the initial guess for the optimizer
        """
        r1, r2, r3 = list(self.beacons_dict.values())[0:3]
        x1, y1 = self.beacons_pos_array[0]
        x2, y2 = self.beacons_pos_array[1]
        x3, y3 = self.beacons_pos_array[2]

        c = (r1**2 - r2**2 + y2**2 + x2**2 - y1**2 - x1**2 ) / 2
        b = (y2 - y1)
        a = (x2 - x1)

        t = (r1**2 - r3**2 + y3**2 + x3**2 - y1**2 - x1**2 ) / 2
        s = (y3 - y1)
        r = (x3 - x1)

        y = ( c*r - t*a ) / ( b*r - s*a )
        x = ( c - b*y ) / a

        return [x, y]

    def lm_optimize(self) -> np.ndarray:
        """
        Use the sympy Levenberg-Marquardt algorithm implementation for multilateration
        """
        return least_squares(self.residuals, self.triangulate(), args=(self.beacons_pos_array, list(self.beacons_dict.values())), method='lm').x

    def calculate_position(self) -> None:
        """
        "Data validation" and console output

        A return should be added instead of a console output
        """
        if not None in self.beacons_dict.values():
            result = self.lm_optimize()
            self.log.info(f"Position calculated: {result[0]:.4f}, {result[1]:.4f}")
        else:
            self.log.error(f"There are beacons that haven't reported distance yet")

async def main():
    base_time = time.time()

    log.debug(f"Loading beacon configuration")

    try:
        beacon_manager = beaconManager("beacon-config.csv")

    except FileNotFoundError:
        log.critical(f"Error loading beacon configuration - File not found")
        raise

    else:
        log.info(f"Beacon configuration loaded\t{dt(base_time)}")

        while True:
            await asyncio.sleep(5)
            beacon_manager.calculate_position()

if __name__ == '__main__':
    start_time = time.time()

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", help="Increase output verbosity", action="store_true")

    parser.add_argument("-l", "--logging", help="Activate logging", action="store_true")

    parser.add_argument("-m", "--mute", help="Deactivate printing, overwritten by --debug", action="store_true")

    args = parser.parse_args()

    start_datetime = time.strftime("%Y-%m-%d %H %M %S")

    console_handler = logging.StreamHandler(sys.stdout)
    log = logging.getLogger("Logger")

    if args.debug:
        console_handler.setLevel(logging.DEBUG)
        log.setLevel(logging.DEBUG)

    elif args.mute:
        console_handler.setLevel(logging.CRITICAL)
        log.setLevel(logging.CRITICAL)
    
    else:
        console_handler.setLevel(logging.INFO)
        log.setLevel(logging.INFO)

    console_handler.setFormatter(ColoredFormatter(log_format))
    log.addHandler(console_handler)

    if args.logging:
        if args.debug:
            file_handler = logging.FileHandler(f'./logs/server-debug {start_datetime}.log', encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(log_format))
        else:
            file_handler = logging.FileHandler(f'./logs/server {start_datetime}.log', encoding="utf-8")
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(logging.Formatter(log_format))
        
        log.addHandler(file_handler)

    log.info('Started')
    log.debug(f"Start datetime: {start_datetime}")

    #TODO: Graceful termination
    try:
        asyncio.run(main())
    except:
        log.critical(f"Program interrupter - Runtime: {runtime(start_time)}")
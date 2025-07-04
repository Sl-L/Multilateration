import time
import numpy as np
from scipy.optimize import least_squares

import pandas as pd

import asyncio

"""
TODO: Implement comms with beacons
"""

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

def dt(base_time: float) -> str:
    """
    Delta time
    """
    return f'\t({(1000*(time.time() - base_time)):.2f} ms)'

def runtime(start_time: float) -> str:
    return f'({((time.time() - start_time)):.2f} s)'

class beaconManager:
    def __init__(self, dataset: str):
        beacons = pd.read_csv(dataset)
        self.beacons_pos_array = beacons[['pos_x', 'pos_y']].to_numpy()
        self.beacons_dict = dict.fromkeys(beacons['beacon_id'], None)

    def update_beacon_distance(self, id, distance):
        if id in self.beacons_dict:
            self.beacons_dict[id] = distance
        
        else:
            # TODO: proper reporting
            print("New beacon id fed on update")

    def residuals(p, beacons, distances):
        x, y = p
        return np.sqrt((x - beacons[:, 0])**2 + (y - beacons[:, 1])**2) - distances
    
    def triangulate(self) -> list[float, float]: # For initial guess
        r1, r2, r3 = list(self.beacons_dict.values())[0:3]
        x1, y1 = self.beacons_pos_array[0]
        x2, y2 = self.beacons_pos_array[1]
        x3, y3 = self.beacons_pos_array[2]

        c = (r1**2 - r2**2 + y2**2 + x2**2 - y1**2 - x1**2 ) / 2
        b = (y2 - y1)
        a = (x2 - x1)

        t = (r1^2 - r3^2 + y3^2 + x3^2 - y1^2 - x1^2 ) / 2
        s = (y3 - y1)
        r = (x3 - x1)

        y = ( c*r - t*a ) / ( b*r - s*a )
        x = ( c - b*y ) / a

        return [x, y]

    def lm_optimize(self) -> np.ndarray:
        return least_squares(self.residuals, self.triangulate(), args=(self.beacons_pos_array, list(self.beacons_dict.values())), method='lm').x

    def calculate_position(self):
        """
        A return should be added
        """
        if not None in self.beacons_dict.values():
            print(self.lm_optimize())
        else:
            print(f"{ts.FAIL}There are beacons that haven't reported distance yet{ts.ENDC}")

async def main():
    base_time = time.time()

    print(time.strftime("%H:%M:%S %d/%m/%Y"))
    print(f"{ts.HEADER}Loading beacon configuration{ts.ENDC}")

    try:
        beacon_manager = beaconManager("beacon-config.csv")

    except FileNotFoundError:
        print(f'\n{ts.FAIL}Error loading beacon configuration - File not found{dt(base_time)}{ts.ENDC}')
        raise

    else:
        print(f"{ts.OK}Beacon configuration loaded{dt(base_time)}{ts.ENDC}")

        while True:
            await asyncio.sleep(5)
            beacon_manager.calculate_position()

if __name__ == '__main__':
    start_time = time.time()

    #TODO: Graceful termination
    try:
        asyncio.run(main())
    except:
        print(f"\n{ts.WARNING}Program interrupted - Runtime: {runtime(start_time)}{ts.ENDC}\n")
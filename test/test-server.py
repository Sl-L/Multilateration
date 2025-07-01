"""Loads dataset of beacon positions, waits for data and calculates position"""

import numpy as np
from scipy.optimize import least_squares

import pandas as pd

class beaconManager:
    def __init__(self, beacons_pos_array: np.ndarray, beacon_ids: pd.Series):
        self.beacons_pos_array = beacons_pos_array
        self.beacons_dict: dict[int, float] = dict.fromkeys(beacon_ids, None)

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
        if not None in self.beacons_dict.values():
            print(self.lm_optimize())

def load_beacon_dataset(dataset: str) -> beaconManager:
    beacons = pd.read_csv(dataset)
    
    return beaconManager(beacons[['pos_x', 'pos_y']].to_numpy(), beacons['beacon_id'])


if __name__ == '__main__':
    bM = load_beacon_dataset("beacon-config-dataset-1.csv")
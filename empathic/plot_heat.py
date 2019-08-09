#!/usr/bin/env python3
import requests
import json
import numpy as np
import pylab as plt

api = 'http://192.168.1.7/empathic'

def main():
    r = requests.post(api + '/heat')
    data = json.loads(r.text)

    heatmap = np.array([[0] * 10] * 16, dtype=float)

    for row in data:
        row = row.split(",")
        x = float(row[0])
        y = float(row[1])
        w = float(row[2])
        ix = int(heatmap.shape[0] * x)
        iy = int(heatmap.shape[1] * y)
        heatmap[ix, iy] = w
            
    plt.imshow(heatmap, cmap='hot')
    plt.show()


if __name__ == '__main__':
    main()

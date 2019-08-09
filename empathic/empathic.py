#!/usr/bin/env python3
from flask import Flask, request
from flask_api import status
from werkzeug import abort
import numpy as np
import json
import uuid
import sys
import tempfile
import os
from contextlib import contextmanager
import pickle

app = Flask(__name__)

tmpdir = tempfile.gettempdir()
lockfile = os.path.join(tmpdir, 'empathic.lock')
datafile = os.path.join(tmpdir, 'empathic.dat')


def acquire_lock():
    while True:
        try:
            with open(lockfile, "x") as _:
                break
        except FileExistsError:
            pass

        
def release_lock():
    try:
        os.unlink(lockfile)
    except:
        pass


@contextmanager
def lock(write=False):
    acquire_lock()
    data = read_data()
    try:
        yield data
    finally:
        if write:
            write_data(data)
        release_lock()
        

class Data:
    def __init__(self):
        self.heatmap = np.array([[0] * 100] * 160, dtype=float)
        self.states = {}  # session -> state


class State:
    def __init__(self, ix, iy):
        self.ix = ix
        self.iy = iy


def read_data():
    try:
        with open(datafile, 'rb') as f:
            return pickle.load(f)
    except:
        return Data()


def write_data(data):
    try:
        with open(datafile, 'wb') as f:
            pickle.dump(data, f)
    except:
        pass
    

def get_coordinate(value):
    try:
        value = float(value)
    except:
        abort(status.HTTP_400_BAD_REQUEST)
    if value < 0 or value > 1:
        abort(status.HTTP_400_BAD_REQUEST)
    return value


@app.route('/press', methods=["POST"])
def press():
    s = request.form.get("s")
    x = request.form.get("x")
    y = request.form.get("y")
    if x is None or y is None or s is None:
        abort(status.HTTP_400_BAD_REQUEST)

    x = get_coordinate(x)
    y = get_coordinate(y)

    with lock(True) as data:
        ix = int(data.heatmap.shape[0] * x)
        iy = int(data.heatmap.shape[1] * y)

        st = data.states.get(s)

        if st is not None:
            data.heatmap[st.ix, st.iy] -= 1

        data.heatmap[ix, iy] += 1
        
        data.states[s] = State(ix, iy)

    return '', status.HTTP_200_OK


@app.route('/release', methods=["POST"])
def release():
    s = request.form.get("s")
    if s is None:
        abort(status.HTTP_400_BAD_REQUEST)

    with lock(True) as data:
        st = data.states.get(s)

        if st is not None:
            data.heatmap[st.ix, st.iy] -= 1
            del data.states[s]

    return '', status.HTTP_200_OK


@app.route('/heat', methods=["POST"])
def heat():
    with lock() as data:
        heatmap = np.copy(data.heatmap)

    heatsum = np.sum(np.sum(heatmap))
    if heatsum > 0:
        heatnorm = heatmap / heatsum
    else:
        heatnorm = heatmap

    rows = []
    for i in range(heatnorm.shape[0]):
        for j in range(heatnorm.shape[1]):
            value = heatnorm[i, j]
            if value >= 0.01:
                row = "{},{},{}".format(round(i / heatnorm.shape[0], 2),
                                        round(j / heatnorm.shape[1], 2),
                                        round(value, 2))
                rows.append(row)

    return json.dumps(rows), status.HTTP_200_OK


@app.route('/', methods=["GET"])
def root():
    return "This is Empathic.", status.HTTP_200_OK


@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "max-age=0, no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r


def main():
    debug = len(sys.argv) > 1 and sys.argv[1] == "debug"
    app.run(debug=debug)


if __name__ == "__main__":
    main()

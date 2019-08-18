#!/usr/bin/env python3
from flask import Flask, request, render_template
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
import logging
from collections import namedtuple

tmpdir = tempfile.gettempdir()

lockfile = os.path.join(tmpdir, 'empathic.lock')
datafile = os.path.join(tmpdir, 'empathic.dat')

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(process)d - %(funcName)s - %(message)s',
                    handlers=[logging.FileHandler(os.path.join(tmpdir, "empathic.log")),
                              logging.StreamHandler()])

logger = logging.getLogger(__name__)

app = Flask(__name__)


def acquire_lock():
    while True:
        try:
            with open(lockfile, "x") as _:
                logger.debug("acquired lock")
                break
        except FileExistsError:
            pass


def release_lock():
    try:
        os.unlink(lockfile)
    except:
        pass
    finally:
        logger.debug("released lock")


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
    SIZE = 96
    def __init__(self):
        self.heatmap = np.array([0] * (Data.SIZE * Data.SIZE), dtype=float)
        self.states = {}  # session -> state


State = namedtuple('State', 'ix iy')


def read_data():
    if not os.path.exists(datafile):
        return Data()
    try:
        with open(datafile, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        logger.exception(e.message)
        return Data()


def write_data(data):
    try:
        with open(datafile, 'wb') as f:
            pickle.dump(data, f)
    except Exception as e:
        logger.exception(e.message)


def get_coordinate(value):
    try:
        value = float(value)
    except:
        abort(status.HTTP_400_BAD_REQUEST)
    if value < 0 or value > 1:
        abort(status.HTTP_400_BAD_REQUEST)
    return value


def index(ix, iy):
    return iy * Data.SIZE + ix


@app.route('/api/press', methods=["POST"])
def press():
    logger.debug("request args: %s", request.form)
    s = request.form.get("s")
    x = request.form.get("x")
    y = request.form.get("y")
    if x is None or y is None or s is None:
        abort(status.HTTP_400_BAD_REQUEST)

    x = get_coordinate(x)
    y = get_coordinate(y)

    with lock(True) as data:
        ix = int(round(Data.SIZE * x))
        iy = int(round(Data.SIZE * y))

        st = data.states.get(s)

        logger.debug("ix = %d, iy = %d, state = %s", ix, iy, st)

        if st is not None:
            data.heatmap[index(st.ix, st.iy)] -= 1

        data.heatmap[index(ix, iy)] += 1
        
        data.states[s] = State(ix, iy)

    return '', status.HTTP_200_OK


@app.route('/api/release', methods=["POST"])
def release():
    logger.debug("request args: %s", request.form)
    s = request.form.get("s")
    if s is None:
        abort(status.HTTP_400_BAD_REQUEST)

    with lock(True) as data:
        st = data.states.get(s)

        logger.debug("state = %s", st)

        if st is not None:
            data.heatmap[index(st.ix, st.iy)] -= 1
            del data.states[s]

    return '', status.HTTP_200_OK


@app.route('/api/heat', methods=["POST"])
def heat():
    logger.debug("request args: %s", request.form)
    with lock() as data:
        heatmap = np.copy(data.heatmap)

    logger.debug(heatmap.shape)
    heatsum = heatmap.sum()
    logger.debug("heatsum = %s", heatsum)
    if heatsum > 0:
        heatnorm = heatmap / heatsum
    else:
        heatnorm = heatmap

    rows = []
    for iy in range(Data.SIZE):
        for ix in range(Data.SIZE):
            value = heatnorm[index(ix, iy)]
            if value >= 0.01:
                row = "{},{},{}".format(round(ix / Data.SIZE, 15),
                                        round(iy / Data.SIZE, 15),
                                        round(value, 15))
                rows.append(row)

    logger.debug("rows = %s", rows)
    return json.dumps(rows), status.HTTP_200_OK


@app.route('/', methods=["GET"])
def root():
    return render_template('index.html'), status.HTTP_200_OK


@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "max-age=0, no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers["Access-Control-Allow-Origin"] = "*"
    r.headers["Access-Control-Allow-Headers"] = "Origin, Content-Type, Accept"
    return r


def main():
    debug = len(sys.argv) > 1 and sys.argv[1] == "debug"
    app.run(debug=debug)


if __name__ == "__main__":
    main()

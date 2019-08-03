from flask import Flask, request
from flask_api import status
from werkzeug import abort
import numpy as np
import json

app = Flask(__name__)

heatmap = np.array([[0] * 100] * 160, dtype=float)

class State:
    def __init__(self, ix, iy):
        self.ix = ix
        self.iy = iy

states = {}  # session -> state


def get_coordinate(value):
    try:
        value = float(value)
    except:
        abort(status.HTTP_400_BAD_REQUEST)
    if value < 0 or value > 1:
        abort(status.HTTP_400_BAD_REQUEST)
    return value


@app.route('/press', methods=["POST"])
def action():
    s = request.form.get("s")
    x = request.form.get("x")
    y = request.form.get("y")
    if x is None or y is None or s is None:
        abort(status.HTTP_400_BAD_REQUEST)

    x = get_coordinate(x)
    y = get_coordinate(y)

    ix = int(heatmap.shape[0] * x)
    iy = int(heatmap.shape[1] * y)

    st = states.get(s)

    if st is not None:
        heatmap[st.ix, st.iy] -= 1

    heatmap[ix, iy] += 1
        
    states[s] = State(ix, iy)

    return '', status.HTTP_200_OK


@app.route('/release', methods=["POST"])
def release():
    s = request.form.get("s")
    if s is None:
        abort(status.HTTP_400_BAD_REQUEST)

    st = states.get(s)

    if st is not None:
        heatmap[st.ix, st.iy] -= 1
        del states[s]

    return '', status.HTTP_200_OK


@app.route('/heat', methods=["POST"])
def heat():
    s = request.form.get("s")
    if s is None:
        abort(status.HTTP_400_BAD_REQUEST)

    heatsum = np.sum(np.sum(heatmap))
    if heatsum > 0:
        heatnorm = heatmap / heatsum
    else:
        heatnorm = heatmap
    data = []
    for i in range(heatnorm.shape[0]):
        for j in range(heatnorm.shape[1]):
            value = heatnorm[i, j]
            if value >= 0.01:
                row = "{},{},{}".format(round(i / heatnorm.shape[0], 2),
                                        round(j / heatnorm.shape[1], 2),
                                        round(value, 2))
                data.append(row)
    return json.dumps(data)


def main():
    app.run("localhost", 7878, debug=True)


if __name__ == "__main__":
    main()

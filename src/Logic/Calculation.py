# A0 = -0.0255
# A1 = 0.01491
import math

A0 = -0.0442
A1 = 0.02121


def truncate(f, n):
    return math.floor(f * 10 ** n) / 10 ** n


def ev_to_px(ev):
    if type(ev) is str:
        return int((float(ev) + A0) / A1)
    return int((ev + A0) / A1)


def px_to_ev(px):
    if type(px) is str:
        return truncate((int(px) * A1) - A0, 4)
    return truncate((px * A1) - A0, 4)


def calculate_intensity_in_range(rng, intensity_range):
    rng = list(map(int, rng))
    intensity = 0
    for px in rng:
        intensity += intensity_range[px]
    return intensity

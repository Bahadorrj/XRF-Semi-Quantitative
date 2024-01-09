import math
# A0 = -0.0255
# A1 = 0.01491
# A0 = -0.0264
# A1 = 0.01518
A0 = -0.0255
A1 = 0.01491


def truncate(f, n):
    return math.floor(f * 10 ** n) / 10 ** n


def ev_to_px(ev):
    return round((float(ev) - A0) / A1)


def px_to_ev(px):
    return truncate((int(px) * A1) + A0, 4)


def calculate_intensity_in_range(rng, intensity_range):
    # -1 is for conflict
    start = rng[0]
    stop = rng[1]
    intensity = 0
    for px in range(start, stop + 1):
        intensity += intensity_range[px]
    return intensity


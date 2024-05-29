import math

A0 = -0.0255
A1 = 0.01491


def truncate(f, n):
    return math.floor(f * 10 ** n) / 10 ** n


def evToPx(ev: float) -> float:
    return (ev - A0) / A1


def pxToEv(px: float) -> float:
    result = (px * A1) + A0
    return truncate(result, 5) if result > 0 else 0

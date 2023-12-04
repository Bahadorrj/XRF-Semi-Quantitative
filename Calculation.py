A0 = -0.0255
A1 = 0.01491

def ev_to_px(ev):
    return round((ev + A0) / A1)


def px_to_ev(px):
    return (px * A1) - A0


def calculate_intensity_in_range(low, high, intensity_range):
    intensity = 0
    for px in range(ev_to_px(low), ev_to_px(high)):
        intensity += intensity_range[px]
    return intensity


def raw_intensity(df, list_counts, rng):
    intensity = list()
    ka1 = df['Ka1']
    la1 = df['La1']
    for element in range(rng):
        if ka1[element] < 30:
            start = ev_to_px(ka1[element] - 0.2)
            finish = ev_to_px(ka1[element] + 0.2)
        else:
            start = ev_to_px(la1[element] - 0.2)
            finish = ev_to_px(la1[element] + 0.2)

        temp = 0
        for px in range(start, finish):
            temp = temp + list_counts[px]
        intensity.append(temp)
    return intensity


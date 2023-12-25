# A0 = -0.0255
# A1 = 0.01491
A0 = -0.0442
A1 = 0.02121


def ev_to_px(ev):
    print(round((ev + A0) / A1))
    return round((ev + A0) / A1)


def px_to_ev(px):
    return (px * A1) - A0


def calculate_intensity_in_range(low, high, intensity_range):
    intensity = 0
    low_px = ev_to_px(low)
    high_px = ev_to_px(high)
    for px in range(low_px, high_px):
        # print(px)
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


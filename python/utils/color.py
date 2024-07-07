def interpolateColor(color1, color2, factor: float) -> tuple:
    """Interpolate between two RGB colors."""
    return tuple(int(a + (b - a) * factor) for a, b in zip(color1, color2))


def rgbToHex(rgb: tuple) -> str:
    """Convert an RGB color to a hex string."""
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def generateGradiant(size: int) -> list:
    green = (127, 255, 212)
    gray = (128, 128, 128)
    gradient = []

    if size <= 1:
        return [rgbToHex(green) for _ in range(size)]

    for i in range(size):
        factor = i / (size - 1)
        color = interpolateColor(green, gray, factor)
        gradient.append(rgbToHex(color))

    return gradient

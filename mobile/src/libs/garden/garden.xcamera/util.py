def darker(color, factor=0.5):
    r, g, b, a = color
    r *= factor
    g *= factor
    b *= factor
    return r, g, b, a

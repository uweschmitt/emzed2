
def getColors(i, light=False):
    colors = [(0, 0, 200), (70, 70, 70), (0, 150, 0), (200, 0, 0), (200, 200, 0), (100, 70, 0)]
    c = colors[i % len(colors)]
    color = "#" + "".join("%02x" % v for v in c)
    if light:
        color = turn_light(color)
    return color


def turn_light(color):
    rgb = [int(color[i:i + 2], 16) for i in range(1, 6, 2)]
    rgb_light = [min(ii + 50, 255) for ii in rgb]
    return "#" + "".join("%02x" % v for v in rgb_light)

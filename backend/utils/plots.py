import numpy as np
import matplotlib.pyplot as plt

from utils.encoding import fig_to_data_uri_under_limit

def scatter_with_regression(
    x, y, x_label="x", y_label="y", title=None,
    line_style="--", line_color="red"
) -> str:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    mask = ~(np.isnan(x) | np.isnan(y))
    x = x[mask]
    y = y[mask]

    slope, intercept = np.polyfit(x, y, 1)
    x_line = np.linspace(x.min(), x.max(), 100)
    y_line = slope * x_line + intercept

    plt.figure(figsize=(6, 4), dpi=110)
    plt.scatter(x, y)
    plt.plot(x_line, y_line, linestyle=line_style, color=line_color)
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    if title:
        plt.title(title)

    uri = fig_to_data_uri_under_limit(fmt="png", max_bytes=100_000)
    plt.close()
    return uri

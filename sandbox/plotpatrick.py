import numpy as np
import pylab
import matplotlib


def plot_heatmap(data, xlabels, ylabels, label_right=True, pad_colorbar=0.2, binsize=None,
                 title=None, cmap="hot", none_color="#777777"):

    """
    plots heatmap including axis labels, colorbar and title

    paramters:
      data        :  2d numpy array
      xlabels     :  list of strings, len is number of colums in data
      ylabels     :  list of strings, len is number of rows in data
      label_right :  boolean, indicates if labels at right of heatmap should be plotted
      pad_colorbar:  float in range 0 .. 1, distance of colorbar to heatmap
      binsize     :  None or float in range 0..1, if this value is not None the heat map and
                     the colorbar are discretised according to this value.
      title       :  None or string
      cmap        :  string with name of colormap, see help(pylab.colormaps) for alternatives
      none_color  :  rgb string for plotting missing values.
    """

    n_rows, n_cols = data.shape
    assert len(xlabels) == n_cols
    assert len(ylabels) == n_rows

    data = np.ma.masked_where(np.isnan(data), data)

    cmap = pylab.cm.get_cmap(cmap)
    cmap.set_bad(none_color)

    if binsize is not None:
        bounds = np.arange(-0.1, 1.001, binsize)
        norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
    else:
        norm = None

    im = pylab.imshow(data, interpolation='none', cmap=cmap, norm=norm)
    pylab.tick_params(axis="both",
                      left="off", bottom="off", top="off", right="off",
                      labelbottom="on", labeltop="on", labelleft="on",
                      labelright="on" if label_right else "off")
    pylab.colorbar(im, pad=pad_colorbar, shrink=0.6)
    axes = im.get_axes()
    axes.set_xticks(range(n_cols))
    axes.set_xticklabels(xlabels)
    axes.set_yticks(range(n_rows))
    axes.set_yticklabels(ylabels)
    im.set_axes(axes)
    if title is not None:
        pylab.title(title, position=(.5, 1.07))  # 1.07 is distance title to plot


def demo():

    # create example matrix
    n_rows = 20
    n_cols = 15
    mat = 0.243 * np.arange(n_rows * n_cols, dtype=float).reshape(n_rows, -1)
    mat = np.abs(np.sin(mat))
    mat[0,0] = None

    # sets only each second label
    xlabels = ["" if i % 2 == 0 else ("%.1f" % i) for i in range(n_cols)]
    ylabels = ["feat %d" % i for i in range(n_rows)]

    pylab.figure(figsize=(7, 10))  # widht, height in inches

    plot_heatmap(mat, xlabels, ylabels, binsize=.1, title="Test HeatMap")
    pylab.show()

if __name__ == "__main__":
    demo()

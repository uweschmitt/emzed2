from guiqwt.config import CONF

def setupCommonStyle(line, marker):

   markerSymbol = "Ellipse" # in this case a circle, because we give only one size parameter.
   edgeColor = "#555555"
   faceColor = "#cc0000"
   alpha = 0.8
   size = 6
   params = {
       "marker/cross/symbol/marker": markerSymbol,
       "marker/cross/symbol/edgecolor": edgeColor,
       "marker/cross/symbol/facecolor": faceColor,
       "marker/cross/symbol/alpha": alpha,
       "marker/cross/symbol/size": size,
       "marker/cross/line/color" : "#000000",
       #"marker/cross/line/width": 0.0,
       "marker/cross/line/style": "NoPen",
       }
   CONF.update_defaults(dict(plot=params))
   marker.markerparam.read_config(CONF, "plot", "marker/cross")
   marker.markerparam.update_marker(marker)
   params = {
       "shape/drag/symbol/marker": markerSymbol,
       "shape/drag/symbol/size": size,
       "shape/drag/symbol/edgecolor": edgeColor,
       "shape/drag/symbol/facecolor": faceColor,
       "shape/drag/symbol/alpha": alpha,

       }
   CONF.update_defaults(dict(plot=params))
   line.shapeparam.read_config(CONF, "plot", "shape/drag")
   line.shapeparam.update_shape(line)

def setupStyleRtMarker(marker):
   linecolor = "#909090"
   edgeColor = "#005500"
   faceColor = "#005500"
   params = {
       "marker/cross/symbol/marker": "Rect",
       "marker/cross/symbol/size": 0,
       "marker/cross/symbol/edgecolor": edgeColor,
       "marker/cross/symbol/facecolor": faceColor,
       "marker/cross/line/color" : linecolor,
       "marker/cross/line/width": 1.0,
       "marker/cross/line/style": "SolidLine",

       "marker/cross/sel_symbol/size": 0,
       "marker/cross/sel_line/color" : linecolor,
       "marker/cross/sel_line/width": 1.0,
       "marker/cross/sel_line/style": "SolidLine",
       }
   CONF.update_defaults(dict(plot=params))
   marker.markerparam.read_config(CONF, "plot", "marker/cross")
   marker.markerparam.update_marker(marker)


def setupStyleRangeMarker(range_):
    params = {
             "range/line/style" : 'SolidLine',
             "range/line/color" : "gray", # "#ff9393",
             "range/line/width" : 1,
             "range/sel_line/style" : 'SolidLine',
             "range/sel_line/color" : "gray", # "red",
             "range/sel_line/width" : 1 + 0* 2,
             "range/fill" : "gray",
             "range/shade" : 0.10,
             "range/symbol/marker" : "Ellipse",
             "range/symbol/size" : 7+1,
             "range/symbol/edgecolor" : "white",
             "range/symbol/facecolor" : "gray", # "#ff9393",
             "range/symbol/alpha" : 1 - 0.2,
             "range/sel_symbol/marker" : "Ellipse",
             "range/sel_symbol/size" : 9-1,
             "range/sel_symbol/edgecolor" : "white",
             "range/sel_symbol/facecolor" : "gray", # "red",
             "range/sel_symbol/alpha" : .9,
             "range/multi/color" : "#806060",
            }

    CONF.update_defaults(dict(histogram=params))
    range_.shapeparam.read_config(CONF, "histogram", "range")
    range_.shapeparam.update_range(range_)

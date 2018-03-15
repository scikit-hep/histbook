import math
import pandas

import vegascope

canvas = vegascope.LocalCanvas()

df = pandas.DataFrame(index=pandas.interval_range(start=0, end=100, freq=10, closed="left"), columns=["sumw"])
df.sumw = [0, 12, 40, 125, 266, 1032, 377, 185, 21, 5]

def plothist(df, level=0):
    ascolumn = df.reset_index(level=level)
    lastrow = ascolumn.iloc[[-1]]
    ascolumn["index"] = ascolumn["index"].apply(lambda x: x.left)
    lastrow["index"] = lastrow["index"].apply(lambda x: x.right)
    ascolumn = pandas.concat([ascolumn, lastrow])
    return altair.Chart(ascolumn).mark_line(interpolate="step-before").encode(x="index", y="sumw")

canvas(plothist(df))

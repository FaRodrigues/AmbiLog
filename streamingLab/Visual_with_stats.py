from bokeh.plotting import figure,show
from bokeh.models import ColumnDataSource, DatetimeTickFormatter, HoverTool
from bokeh.models import Tabs, TabPanel
from bokeh.io import curdoc
from datetime import datetime
import os, xml.etree.ElementTree as ET, pandas as pd

class VisualStats:
    """
    Creates a statistics tab showing hourly mean and standard deviation
    of the chosen channel (e.g. 'TCA') from XML logs under varamblog.
    """
    def __init__(self, data_dir="./varamblog", channel="TCA"):
        self.data_dir = data_dir
        self.channel = channel
        self.source = ColumnDataSource(dict(x=[], mean=[], std=[]))
        # Schedule update every 60 seconds
        curdoc().add_periodic_callback(self.update_stats, 60000)

    def define_plot(self):
        p = figure(
            title="Statistical Summary Over Time", width=800, height=400,
            x_axis_type='datetime'
        )
        p.line(x='x', y='mean', source=self.source, legend_label="Mean")
        p.line(x='x', y='std',  source=self.source, color="red", legend_label="Std Dev")

        p.xaxis.formatter = DatetimeTickFormatter(
            hours="%d/%m %H:%M",
            days="%d/%m %H:%M"
        )
        hover = HoverTool(
            tooltips=[("Time","@x{%F %T}"), ("Mean","@mean"),("Std","@std")],
            formatters={'@x':'datetime'}, mode='vline'
        )
        p.add_tools(hover)
        p.legend.location = "top_left"
        return p

    def update_stats(self):
        records = []
        for root_dir, _, files in os.walk(self.data_dir):
            for fname in files:
                if fname.endswith('.xml'):
                    path = os.path.join(root_dir, fname)
                    try:
                        tree = ET.parse(path)
                        for meas in tree.getroot().iter('measure'):
                            ts = meas.get('timestamp')
                            t = datetime.fromisoformat(ts)
                            node = meas.find(self.channel)
                            if node is None or not node.text:
                                continue
                            val = float(node.text)
                            records.append((t, val))
                    except Exception:
                        continue
        if not records:
            return
        df = pd.DataFrame(records, columns=['t','v']).set_index('t')
        stats = df.resample('1H').agg(['mean','std']).dropna()
        x    = stats.index.to_pydatetime()
        mean = stats['v']['mean'].values
        std  = stats['v']['std'].values
        self.source.data = dict(x=x, mean=mean, std=std)

class VisualWithStats:
    def __init__(self, callbackFunc, running, data_dir="./varamblog"):
        # Import original real-time Visual
        from Visual import Visual as BaseVisual
        base_vis = BaseVisual(callbackFunc, running)

        # TabPanel for real-time
        tab_rt = TabPanel(child=base_vis.layout(), title="Real-Time")

        # TabPanel for stats
        stats_vis = VisualStats(data_dir)
        tab_stats = TabPanel(child=stats_vis.define_plot(), title="Statistics")

        tabs = Tabs(tabs=[tab_rt, tab_stats])
        doc = curdoc()
        self.doc = doc
        doc.clear()
        doc.add_root(tabs)
        doc.title = "StreamLab with Stats"

# In your main.py, swap:
#    from Visual import Visual
# for:
#    from Visual_with_stats import VisualWithStats as Visual

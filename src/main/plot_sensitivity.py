from os.path import dirname, join

import numpy as np
import pandas.io.sql as psql
from bokeh.plotting import figure
from bokeh.layouts import layout, widgetbox
from bokeh.models import ColumnDataSource, HoverTool, Div
from bokeh.models.widgets import Slider, Select, TextInput
from bokeh.io import curdoc
import numpy as np
import scipy
import pandas as pd
from predicter import predicter
from bokeh.models.widgets import Panel, Tabs, TextInput
from bokeh.models import Range1d
from bokeh.palettes import Spectral5
my_predicter = predicter("../../data/nba.db")

COLORS = Spectral5

"""
Tab 2: Totaly Flexible
"""
# Create Input controls

class sensitivity_maker (object):
    def __init__ (self, size=500):
        self.size = size
        self.game_thresh= Slider(title="Probability of Winning at Least Games", value=50, start=0, end=82, step=1)
        self.select_team = Select(title="Current_Team:", value="GSW", options=my_predicter.get_teams_list())

# Create Column Data Source that will be used by the plot
        self.scatter_source = ColumnDataSource(data=dict(
                    pct =[],
                    we = [],
                    prob = []
                    ))
                    

        self.p2_hover = HoverTool(
            tooltips=[
                ("win percentage", "@pct")
                ("game equivalent", "@we"),
                ("probability of winnin N games", "@prob"),
            ]
        )

        self.p2 = figure(title="Probability of winning at least n games", tools=[self.p2_hover,"save"],
                   background_fill="#E8DDCB",  width= self.size, plot_height=self.size)
        self.p2.xaxis.axis_label = 'Prior Expected Win Pct'
        self.p2.yaxis.axis_label = 'Prior Game Equivalent'
        groups = pd.qcut(self.scatter_source.prob, len(COLORS))
        c = [COLORS[xx] for xx in groups.codes]
        self.p2.circle(x='pct', y='we', color= c, line_color="black", source = self.scatter_source, size = 40)
  
    def select_data(self):
        return my_predicter.calc_sensitivity (
            self.select_team.value
            self.max_percentile.value)


    def update(self):
        data_dict = self.select_data()
        hist, edges = np.histogram(data_dict['prior_hist'].pct, density=True, bins=25)
        x = np.linspace(0, 1, 1000)
        self.scatter_source.data = data_dict


    def main(self):
        controls = [self.game_thresh, self.select_team
        for control in controls:
            control.on_change('value', lambda attr, old, new: self.update())

        sizing_mode = 'fixed'  # 'scale_width' also looks nice with this example

        else:
            l1 = layout([
            [inputs],
            [self.p2],
            ], sizing_mode=sizing_mode)
        self.update()  # initial load of the data
        return l1


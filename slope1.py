from datetime import datetime, timedelta

from bokeh.plotting import figure, show, output_file
from bokeh.models import HoverTool, DatetimeTickFormatter

# --- Parameters ---
start_value = 50.0
slope_per_min = 0.2567
n_minutes = 24 * 60          # number of minutes to plot (here: 24 hours)
start_time = datetime(2026, 11, 8, 0, 0)

# --- Data ---
times = [start_time + timedelta(minutes=i) for i in range(n_minutes + 1)]
var_d = [start_value + slope_per_min * i for i in range(n_minutes + 1)]

# --- Plot ---
output_file("var_d.html")

p = figure(
    title="var_d vs Time",
    x_axis_type="datetime",
    x_axis_label="Time",
    y_axis_label="var_d",
    width=900,
    height=450,
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

p.line(times, var_d, line_width=2, color="firebrick", legend_label="var_d")
p.scatter(times[::60], var_d[::60], size=5, color="firebrick")  # hourly markers

p.add_tools(
    HoverTool(
        tooltips=[("Time", "@x{%F %H:%M}"), ("var_d", "@y{0.000}")],
        formatters={"@x": "datetime"},
        mode="vline",
    )
)

p.xaxis.formatter = DatetimeTickFormatter(hours="%H:%M", days="%d %b %H:%M")
p.legend.location = "top_left"

show(p)

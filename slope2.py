from datetime import datetime, timedelta

from bokeh.plotting import figure, show, output_file
from bokeh.models import HoverTool, DatetimeTickFormatter

# --- Controller parameters ---
error = 0.8                  # constant error, deg C
Kp = 72.5
Ki = 0.99175                 # per minute

n_minutes = 24 * 60
start_time = datetime(2026, 11, 8, 0, 0)

# --- Data: u(t) = Kp*e + Ki*e*t ---
times = [start_time + timedelta(minutes=i) for i in range(n_minutes + 1)]
var_d = [Kp * error + Ki * error * i for i in range(n_minutes + 1)]

# --- Plot ---
output_file("var_d.html")

p = figure(
    title="var_d vs Time (PI response, e = 0.8 °C)",
    x_axis_type="datetime",
    x_axis_label="Time",
    y_axis_label="var_d",
    width=900,
    height=450,
    tools="pan,wheel_zoom,box_zoom,reset,save",
)

p.line(times, var_d, line_width=2, color="firebrick", legend_label="var_d")
p.scatter(times[::60], var_d[::60], size=5, color="firebrick")

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

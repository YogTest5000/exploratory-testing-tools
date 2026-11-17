
from datetime import datetime, timedelta

from bokeh.plotting import figure, show, output_file
from bokeh.models import (
    ColumnDataSource,
    HoverTool,
    Span
)
from bokeh.layouts import column
from bokeh.io import save

# -----------------------------------
# PI Controller Parameters
# -----------------------------------

setpoint = 25.0
room_temperature = 24.5

Kp = 20.0
Ki = 0.125

output_min = 50
output_max = 200

update_interval = 1       # Minutes
simulation_duration = 720 # 12 hours

# -----------------------------------
# Initial Values
# -----------------------------------

integral = 0.0
start_time = datetime.now().replace(second=0, microsecond=0)

timestamps = []
raw_outputs = []
clamped_outputs = []
integral_values = []
proportional_values = []

error = setpoint - room_temperature

# -----------------------------------
# PI Controller Simulation
# -----------------------------------

for minute in range(simulation_duration + 1):

    current_time = start_time + timedelta(minutes=minute)

    # Proportional calculation
    proportional = Kp * error

    # Integral calculation
    if minute > 0:
        integral += Ki * error * update_interval

    # Raw PI output
    raw_output = proportional + integral

    # Output clamping
    output = max(output_min, min(output_max, raw_output))

    # Store results
    timestamps.append(current_time)
    raw_outputs.append(raw_output)
    clamped_outputs.append(output)
    integral_values.append(integral)
    proportional_values.append(proportional)

# -----------------------------------
# Create Bokeh Data Source
# -----------------------------------

source = ColumnDataSource(data=dict(
    time=timestamps,
    raw=raw_outputs,
    output=clamped_outputs,
    integral=integral_values,
    proportional=proportional_values
))

# -----------------------------------
# Create Bokeh Figure
# -----------------------------------

p = figure(
    title="PI Controller Output with Clamping",
    x_axis_type="datetime",
    x_axis_label="DateTime",
    y_axis_label="Controller Output",
    width=1100,
    height=550,
    tools="pan,wheel_zoom,box_zoom,reset,save"
)

# Raw PI output
p.line(
    x="time",
    y="raw",
    source=source,
    line_width=2,
    color="blue",
    legend_label="Unclamped PI Output"
)

# Clamped output
p.line(
    x="time",
    y="output",
    source=source,
    line_width=3,
    color="green",
    legend_label="Clamped PI Output"
)

# Minimum clamp
p.add_layout(Span(
    location=output_min,
    dimension="width",
    line_color="red",
    line_dash="dashed",
    line_width=2
))

# Maximum clamp
p.add_layout(Span(
    location=output_max,
    dimension="width",
    line_color="orange",
    line_dash="dashed",
    line_width=2
))

# Hover information
hover = HoverTool(
    tooltips=[
        ("DateTime", "@time{%F %T}"),
        ("Proportional", "@proportional{0.00}"),
        ("Integral", "@integral{0.0000}"),
        ("Raw Output", "@raw{0.00}"),
        ("Clamped Output", "@output{0.00}")
    ],
    formatters={
        "@time": "datetime"
    },
    mode="vline"
)

p.add_tools(hover)

p.legend.location = "top_left"
p.legend.click_policy = "hide"

p.y_range.start = 0
p.y_range.end = 210

p.xaxis.major_label_orientation = 0.8

p.grid.grid_line_alpha = 0.3

# -----------------------------------
# Save and Display
# -----------------------------------

output_file("pi_controller_bokeh.html")

show(p)

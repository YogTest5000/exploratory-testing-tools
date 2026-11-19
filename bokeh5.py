
import pandas as pd

from bokeh.plotting import figure, show
from bokeh.models import HoverTool

# Read CSV file
df = pd.read_csv("temperature.csv")

# Merge date and time columns into datetime
df["datetime"] = pd.to_datetime(
    df["date"].astype(str) + " " + df["time"].astype(str)
)

# Sort data by datetime
df = df.sort_values("datetime")

# Create Bokeh figure
p = figure(
    title="Temperature vs DateTime",
    x_axis_type="datetime",
    width=1000,
    height=500,
    x_axis_label="Date and Time",
    y_axis_label="Temperature (Celsius)",
    tools="pan,wheel_zoom,box_zoom,reset,save"
)

# Plot line chart
p.line(
    x=df["datetime"],
    y=df["temperature"],
    line_width=2,
    legend_label="Temperature"
)

# Add data point markers
p.scatter(
    x=df["datetime"],
    y=df["temperature"],
    size=6,
    marker="circle"
)

# Add hover information
hover = HoverTool(
    tooltips=[
        ("DateTime", "@x{%F %T}"),
        ("Temperature", "@y{0.00}")
    ],
    formatters={
        "@x": "datetime"
    },
    mode="vline"
)

p.add_tools(hover)

p.legend.location = "top_left"

# Display chart
show(p)

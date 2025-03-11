import argparse
import pandas as pd
import os
from bokeh.plotting import figure, output_file, save, show
from bokeh.models import DatetimeTickFormatter

def plot_csv(file_name, columns):
    # Check if the file exists
    if not os.path.exists(file_name):
        print(f"Error: File '{file_name}' not found.")
        return
    
    # Load CSV file
    try:
        df = pd.read_csv(file_name, parse_dates=[0])
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # Ensure datetime format in the first column
    time_column = df.columns[0]
    df[time_column] = pd.to_datetime(df[time_column])

    # Check if specified columns exist
    missing_cols = [col for col in columns if col not in df.columns]
    if missing_cols:
        print(f"Error: Columns {missing_cols} not found in the CSV file.")
        return

    # Create a Bokeh plot
    output_file("bokeh_plot.html")
    p = figure(title="CSV Data Visualization", x_axis_label="Time", x_axis_type="datetime", width=800, height=500)

    # Format the x-axis for better datetime display
    p.xaxis.formatter = DatetimeTickFormatter(
        hours="%H:%M:%S",
        days="%Y-%m-%d",
        months="%Y-%m",
        years="%Y"
    )

    # Plot each specified column
    for col in columns:
        p.line(df[time_column], df[col], legend_label=col, line_width=2)

    # Save and show the plot
    save(p)
    print("Plot saved as 'bokeh_plot.html'. Open this file in a browser.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot specified columns from a CSV file using Bokeh.")
    parser.add_argument("file", help="CSV file containing data.")
    parser.add_argument("columns", nargs="+", help="Columns to plot (space-separated).")

    args = parser.parse_args()
    plot_csv(args.file, args.columns)

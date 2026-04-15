import pandas as pd
import re
from bokeh.plotting import figure, show, output_file
from bokeh.models import ColumnDataSource, HoverTool
from bokeh.palettes import Category10


class TimeSeriesNLPQuerySystem:
    def __init__(self, csv_file, date_column="date"):
        """
        Initialize the NLP query system.

        Args:
            csv_file (str): Path to CSV file
            date_column (str): Name of the datetime column
        """
        self.df = pd.read_csv(csv_file)
        self.date_column = date_column

        if self.date_column not in self.df.columns:
            raise ValueError(f"Date column '{date_column}' not found in CSV")

        self.df[self.date_column] = pd.to_datetime(self.df[self.date_column], errors="coerce")
        self.df = self.df.dropna(subset=[self.date_column])
        self.df = self.df.sort_values(by=self.date_column)
        self.df.set_index(self.date_column, inplace=True)

        self.numeric_columns = self.df.select_dtypes(include="number").columns.tolist()

        if not self.numeric_columns:
            raise ValueError("No numeric columns found in dataset")

        self.metric_aliases = {
            "temp": "temperature",
            "sale": "sales",
            "income": "revenue",
            "order count": "orders"
        }

    def parse_query(self, query):
        """
        Parse natural language query into structured intent.
        """
        query = query.lower().strip()

        parsed = {
            "action": None,
            "metric": None,
            "time_filter": None,
            "plot": False
        }

        if any(word in query for word in ["plot", "chart", "graph", "visualize"]):
            parsed["plot"] = True

        action_map = {
            "average": "mean",
            "mean": "mean",
            "avg": "mean",
            "sum": "sum",
            "total": "sum",
            "max": "max",
            "maximum": "max",
            "min": "min",
            "minimum": "min",
            "count": "count",
            "show": "show",
            "display": "show",
            "list": "show"
        }

        for word, action in action_map.items():
            if word in query:
                parsed["action"] = action
                break

        if parsed["action"] is None:
            parsed["action"] = "show"

        for alias, actual in self.metric_aliases.items():
            if alias in query:
                parsed["metric"] = actual
                break

        if parsed["metric"] is None:
            for col in self.numeric_columns:
                if col.lower() in query:
                    parsed["metric"] = col
                    break

        if parsed["metric"] is None and self.numeric_columns:
            parsed["metric"] = self.numeric_columns[0]

        parsed["time_filter"] = self.extract_time_filter(query)

        return parsed

    def extract_time_filter(self, query):
        """
        Extract time filtering conditions from natural language query.
        """
        today = pd.Timestamp.today().normalize()

        match = re.search(r"last (\d+) days?", query)
        if match:
            days = int(match.group(1))
            start = today - pd.Timedelta(days=days)
            return ("range", start, today)

        match = re.search(r"last (\d+) weeks?", query)
        if match:
            weeks = int(match.group(1))
            start = today - pd.Timedelta(weeks=weeks)
            return ("range", start, today)

        match = re.search(r"last (\d+) months?", query)
        if match:
            months = int(match.group(1))
            start = today - pd.DateOffset(months=months)
            return ("range", start, today)

        if "today" in query:
            return ("range", today, today + pd.Timedelta(days=1))

        if "yesterday" in query:
            start = today - pd.Timedelta(days=1)
            return ("range", start, today)

        if "this month" in query:
            start = today.replace(day=1)
            return ("range", start, today)

        if "this year" in query:
            start = today.replace(month=1, day=1)
            return ("range", start, today)

        match = re.search(r"between (\d{4}-\d{2}-\d{2}) and (\d{4}-\d{2}-\d{2})", query)
        if match:
            start = pd.to_datetime(match.group(1))
            end = pd.to_datetime(match.group(2))
            return ("range", start, end)

        months = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12
        }

        for month_name, month_num in months.items():
            if month_name in query:
                return ("month", month_num)

        return None

    def apply_time_filter(self, df, time_filter):
        """
        Apply extracted time filter to dataframe.
        """
        if time_filter is None:
            return df

        filter_type = time_filter[0]

        if filter_type == "range":
            start, end = time_filter[1], time_filter[2]
            return df[(df.index >= start) & (df.index <= end)]

        if filter_type == "month":
            month_num = time_filter[1]
            return df[df.index.month == month_num]

        return df

    def execute_query(self, query):
        """
        Execute natural language query on time series data.
        """
        parsed = self.parse_query(query)
        filtered_df = self.apply_time_filter(self.df, parsed["time_filter"])

        if filtered_df.empty:
            return "No data found for the requested time period."

        metric = parsed["metric"]
        action = parsed["action"]

        if metric not in filtered_df.columns:
            return f"Metric '{metric}' not found in dataset."

        if parsed["plot"]:
            self.plot_data_bokeh(filtered_df, metric, query)
            return f"Bokeh plot generated for '{metric}'."

        if action == "show":
            return filtered_df[[metric]].tail(20)

        if action == "mean":
            return filtered_df[metric].mean()

        if action == "sum":
            return filtered_df[metric].sum()

        if action == "max":
            return filtered_df[metric].max()

        if action == "min":
            return filtered_df[metric].min()

        if action == "count":
            return filtered_df[metric].count()

        return "Sorry, I could not understand the query."

    def plot_data_bokeh(self, df, metric, title):
        """
        Plot time series data using Bokeh.
        """
        plot_df = df.reset_index().copy()
        plot_df["date_str"] = plot_df[self.date_column].dt.strftime("%Y-%m-%d %H:%M:%S")

        source = ColumnDataSource(plot_df)

        output_file("timeseries_plot.html")

        p = figure(
            title=title,
            x_axis_type="datetime",
            width=1000,
            height=450,
            tools="pan,wheel_zoom,box_zoom,reset,save"
        )

        p.line(
            x=self.date_column,
            y=metric,
            source=source,
            line_width=2,
            color=Category10[10][0],
            legend_label=metric
        )

        p.circle(
            x=self.date_column,
            y=metric,
            source=source,
            size=6,
            color=Category10[10][1]
        )

        hover = HoverTool(
            tooltips=[
                ("Date", "@date_str"),
                (metric, f"@{metric}")
            ],
            mode="vline"
        )

        p.add_tools(hover)
        p.xaxis.axis_label = "Date"
        p.yaxis.axis_label = metric
        p.legend.location = "top_left"
        p.legend.click_policy = "hide"

        show(p)


if __name__ == "__main__":
    csv_file = "timeseries_data.csv"

    system = TimeSeriesNLPQuerySystem(csv_file)

    print("Available numeric columns:", system.numeric_columns)
    print("Type 'exit' to quit.\n")

    while True:
        user_query = input("Enter your query: ").strip()

        if user_query.lower() == "exit":
            break

        try:
            result = system.execute_query(user_query)
            print("\nResult:")
            print(result)
            print("-" * 50)
        except Exception as e:
            print(f"Error: {e}")

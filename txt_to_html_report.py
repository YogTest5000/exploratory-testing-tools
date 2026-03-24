import os

def create_interactive_html_report(output_file="interactive_report.html"):
    data = [
        {"ID": 1, "Name": "Alice", "Department": "QA", "Score": 92},
        {"ID": 2, "Name": "Bob", "Department": "Development", "Score": 85},
        {"ID": 3, "Name": "Charlie", "Department": "DevOps", "Score": 88},
        {"ID": 4, "Name": "David", "Department": "QA", "Score": 79},
        {"ID": 5, "Name": "Eva", "Department": "Management", "Score": 95},
    ]

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive HTML Report</title>

    <!-- DataTables CSS -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.8/css/jquery.dataTables.min.css">

    <!-- jQuery -->
    <script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>

    <!-- DataTables JS -->
    <script src="https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js"></script>

    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 30px;
            background-color: #f4f6f8;
        }}
        h1 {{
            text-align: center;
            color: #333;
        }}
        .container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        table {{
            width: 100%;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Employee Performance Report</h1>
        <table id="reportTable" class="display">
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Department</th>
                    <th>Score</th>
                </tr>
            </thead>
            <tbody>
                {''.join([
                    f"<tr><td>{row['ID']}</td><td>{row['Name']}</td><td>{row['Department']}</td><td>{row['Score']}</td></tr>"
                    for row in data
                ])}
            </tbody>
        </table>
    </div>

    <script>
        $(document).ready(function() {{
            $('#reportTable').DataTable({{
                "pageLength": 5,
                "lengthMenu": [5, 10, 25, 50],
                "ordering": true,
                "searching": true
            }});
        }});
    </script>
</body>
</html>
"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Interactive HTML report created: {os.path.abspath(output_file)}")


if __name__ == "__main__":
    create_interactive_html_report()

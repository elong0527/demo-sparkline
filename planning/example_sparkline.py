#!/usr/bin/env python3
"""
Minimal example of sparkline_point_js to test HTML output.
"""

import polars as pl
from sparkline_point import sparkline_point_js


def create_minimal_example():
    """Create a minimal working example."""

    # Create simple data
    data = pl.DataFrame({"value": [5.1, 4.9, 4.7], "error": [0.3, 0.2, 0.4]})

    # Generate sparkline with mostly default values
    js_code = sparkline_point_js(data, x="value", x_lower="error")

    print(f"Generated {len(js_code)} characters of JavaScript")

    # Create minimal HTML file
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Minimal Sparkline Test</title>
    <script src="https://unpkg.com/react@17/umd/react.production.min.js"></script>
    <script src="https://unpkg.com/react-dom@17/umd/react-dom.production.min.js"></script>
    <script src="https://cdn.plot.ly/plotly-2.18.2.min.js"></script>
</head>
<body>
    <h1>Sparkline Test</h1>
    <div id="sparkline"></div>

    <script>
        // The generated sparkline function
        const renderSparkline = {js_code};

        // Mock cell data
        const cell = {{
            row: {{value: 5.1, error: 0.3}}
        }};

        // Render the sparkline
        const element = renderSparkline(cell, {{}});
        ReactDOM.render(element, document.getElementById('sparkline'));

        console.log('Sparkline rendered successfully');
    </script>
</body>
</html>"""

    with open("test.html", "w") as f:
        f.write(html_content)

    print("Created test.html")


if __name__ == "__main__":
    create_minimal_example()

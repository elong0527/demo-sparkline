#!/usr/bin/env python3
"""
Python implementation of sparkline_point_js for creating interactive
Plotly sparklines in reactable tables.
"""

from pathlib import Path
from string import Template

import polars as pl


def sparkline_point_js(
    tbl: pl.DataFrame,
    x: str | list[str],
    type: str = "cell",
    x_lower: str | list[str] | None = None,
    x_upper: str | list[str] | None = None,
    xlim: tuple[float, float] | None = None,
    xlab: str = "",
    y: list[float] | None = None,
    vline: float | None = None,
    text: str | list[str] | None = None,
    height: float = 30,
    width: float = 150,
    color: str | list[str] = "#FFD700",
    color_errorbar: str | list[str] | None = None,
    color_vline: str = "#00000050",
    legend: bool = False,
    legend_label: list[str] | None = None,
    legend_title: str = "",
    legend_position: float = 0,
    legend_type: str = "point",
    margin: list[int] | None = None,
) -> str:
    """
    Generate JavaScript code for Plotly sparkline visualization.

    Parameters
    ----------
    tbl : pl.DataFrame
        The Polars DataFrame containing the data.
    x : str | list[str]
        Column name(s) for x-axis values.
    type : str
        Type of reactable component ("cell", "footer", "header").
    x_lower : str | list[str] | None
        Column name(s) for lower error bar values.
    x_upper : str | list[str] | None
        Column name(s) for upper error bar values.
    xlim : tuple[float, float] | None
        X-axis limits.
    xlab : str
        X-axis label.
    y : list[float] | None
        Y-axis values for each point.
    vline : float | None
        Position for vertical reference line.
    text : str | list[str] | None
        Hover text for each point.
    height : float
        Height of the plot.
    width : float
        Width of the plot.
    color : str | list[str]
        Point colors.
    color_errorbar : str | list[str] | None
        Error bar colors.
    color_vline : str
        Vertical line color.
    legend : bool
        Whether to show legend.
    legend_label : list[str] | None
        Legend labels.
    legend_title : str
        Legend title.
    legend_position : float
        Legend vertical position.
    legend_type : str
        Type of legend ("point", "line", "point+line").
    margin : list[int] | None
        Margins [bottom, left, top, right, padding].

    Returns
    -------
    str
        JavaScript code for the sparkline visualization.
    """

    # Set defaults
    if margin is None:
        margin = [0, 0, 0, 0, 0]

    if x_upper is None:
        x_upper = x_lower

    if color_errorbar is None:
        color_errorbar = color

    # Convert single values to lists
    if isinstance(x, str):
        x = [x]

    if isinstance(color, str):
        color = [color] * len(x)

    if isinstance(color_errorbar, str):
        color_errorbar = [color_errorbar] * len(x)

    if y is None:
        y = list(range(1, len(x) + 1))

    if text is None:
        text = ['""'] * len(x)
    elif isinstance(text, str):
        text = [text] * len(x)

    # Input validation
    for col in x:
        if col not in tbl.columns:
            raise ValueError(f"Column '{col}' not found in DataFrame")

    if x_lower is not None:
        if isinstance(x_lower, str):
            x_lower = [x_lower] * len(x)
        for col in x_lower:
            if col not in tbl.columns:
                raise ValueError(f"Column '{col}' not found in DataFrame")

    if x_upper is not None:
        if isinstance(x_upper, str):
            x_upper = [x_upper] * len(x)
        for col in x_upper:
            if col not in tbl.columns:
                raise ValueError(f"Column '{col}' not found in DataFrame")

    # Convert colors to RGBA format
    def to_rgba(color_name: str) -> str:
        """Convert color name to rgba string."""
        # Remove whitespace
        color_str = color_name.strip()

        # Check if it's a hex color
        if color_str.startswith("#"):
            try:
                # Remove the '#' and handle 3 or 6 digit hex
                hex_str = color_str[1:]
                if len(hex_str) == 3:
                    hex_str = "".join([c * 2 for c in hex_str])
                if len(hex_str) == 6:
                    r = int(hex_str[0:2], 16)
                    g = int(hex_str[2:4], 16)
                    b = int(hex_str[4:6], 16)
                    return f'"rgba({r}, {g}, {b}, 1)"'
            except ValueError:
                pass

        # Check if it's an rgb/rgba color
        if color_str.lower().startswith("rgb"):
            # Already in the right format, just ensure quotes
            return f'"{color_str}"'

        # For any other format, return as-is (let the browser handle it)
        return f'"{color_name}"'

    # Prepare JavaScript variables
    if type == "cell":
        js_x = ", ".join([f'cell.row["{col}"]' for col in x])
    else:
        js_x = ", ".join(map(str, range(len(color))))

    js_y = ", ".join(map(str, y))

    if x_lower is None or type in ("footer", "header"):
        js_x_lower = "0"
        js_x_upper = "0"
        color_errorbar = ["#FFFFFF00"] * len(x)
    else:
        js_x_lower = ", ".join([f'cell.row["{col}"]' for col in x_lower])
        js_x_upper = ", ".join([f'cell.row["{col}"]' for col in x_upper])

    # Calculate x range if not provided
    if xlim is None:
        x_vals = []
        for col in x:
            col_vals = tbl[col].drop_nulls().to_list()
            x_vals.extend(col_vals)
        if x_vals:
            xlim = (min(x_vals) - 0.5, max(x_vals) + 0.5)
        else:
            xlim = (0, 1)

    js_x_range = f"{xlim[0]}, {xlim[1]}"
    js_y_range = f"0, {len(x) + 1}"

    js_text = ", ".join(text)
    js_vline = str(vline) if vline is not None else "[]"
    js_height = str(height)
    js_width = str(width)

    js_color = ", ".join([to_rgba(c) for c in color])
    js_color_errorbar = ", ".join([to_rgba(c) for c in color_errorbar])
    js_color_vline = to_rgba(color_vline)

    js_xlab = xlab
    js_showlegend = "true" if legend else "false"
    js_legend_title = legend_title
    js_legend_position = str(legend_position)

    # Convert legend type
    legend_type_map = {"point": "markers", "line": "lines", "point+line": "markers+lines"}
    js_legend_type = legend_type_map.get(legend_type, "markers")

    js_legend_label = ", ".join([f'"{label}"' for label in legend_label]) if legend_label else ""
    js_margin = ", ".join(map(str, margin))

    # Create data trace
    data_traces = []
    for i in range(len(x)):
        trace = f"""{{
        "x": [x[{i}]],
        "y": [y[{i}]],
        "error_x": {{
            type: "data",
            symmetric: false,
            array: [x_upper[{i}]],
            arrayminus: [x_lower[{i}]],
            "color": color_errorbar[{i}]
        }},
        "text": text[{i}],
        "hoverinfo": "text",
        "mode": "{js_legend_type}",
        "alpha_stroke": 1,
        "sizes": [10, 100],
        "spans": [1, 20],
        "type": "scatter",
        "name": legend_label[{i}],
        "marker": {{
            "color": [color[{i}]],
            "line": {{
                "color": color[{i}]
            }}
        }},
        "line": {{
            "color": color[{i}]
        }}
    }}"""
        data_traces.append(trace)

    data_trace = ",\n      ".join(data_traces)

    # Read the template from the same directory
    template_path = Path(__file__).parent / "sparkline.js"
    with open(template_path) as f:
        template_content = f.read()

    template = Template(template_content)

    # Substitute variables
    js_code = template.safe_substitute(
        js_x=js_x,
        js_y=js_y,
        js_x_lower=js_x_lower,
        js_x_upper=js_x_upper,
        js_x_range=js_x_range,
        js_y_range=js_y_range,
        js_vline=js_vline,
        js_text=js_text,
        js_height=js_height,
        js_width=js_width,
        js_color=js_color,
        js_color_errorbar=js_color_errorbar,
        js_color_vline=js_color_vline,
        js_margin=js_margin,
        js_xlab=js_xlab,
        js_showlegend=js_showlegend,
        js_legend_title=js_legend_title,
        js_legend_position=js_legend_position,
        js_legend_label=js_legend_label,
        data_trace=data_trace,
    )

    return js_code

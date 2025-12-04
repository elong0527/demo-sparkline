# pyre-strict
"""Core ForestPlot class for forest plot system."""

from typing import Any

import polars as pl
from pydantic import BaseModel, ConfigDict, Field, field_validator

from forestly.core.config import Config
from forestly.panels.base import Panel


class ForestPlot(BaseModel):
    """Main class for creating forest plots from clinical trial data."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    data: pl.DataFrame
    panels: list[Panel]
    config: Config = Field(default_factory=Config)

    @field_validator("data")  # pyre-fixme[56]
    @classmethod
    def validate_data(cls, v: pl.DataFrame) -> pl.DataFrame:
        """Validate input data.

        Args:
            v: Input DataFrame

        Returns:
            Validated DataFrame

        Raises:
            ValueError: If data is empty
        """
        if v.is_empty():
            raise ValueError("Data cannot be empty")
        return v

    @field_validator("panels")  # pyre-fixme[56]
    @classmethod
    def validate_panels(cls, v: list[Panel]) -> list[Panel]:
        """Validate panels.

        Args:
            v: List of panels

        Returns:
            Validated panels

        Raises:
            ValueError: If no panels provided
        """
        if not v:
            raise ValueError("At least one panel must be provided")
        return v

    def model_post_init(self, __context: Any) -> None:
        """Post-initialization validation."""
        self._validate_columns()

    def _validate_columns(self) -> None:
        """Validate that all required columns exist in data.

        Raises:
            ValueError: If required columns are missing
        """
        all_required = set()
        for panel in self.panels:
            all_required.update(panel.get_required_columns())

        available = set(self.data.columns)
        missing = all_required - available

        if missing:
            raise ValueError(f"Missing required columns in data: {missing}")

    def _prepare_reactable_data(self) -> dict[str, Any]:
        """Prepare data for Reactable with nesting.

        Returns:
            Dictionary with prepared data and configuration
        """
        result: dict[str, Any] = {
            "data": self.data,
            "panels": [],
            "config": self.config.model_dump(),
        }

        for panel in self.panels:
            panel_data = panel.render(self.data)
            result["panels"].append(panel_data)

        return result

    def to_reactable(self) -> Any:
        """Generate interactive Reactable table.

        Returns:
            Reactable object
        """
        from pathlib import Path

        from IPython.display import HTML, display

        from forestly.exporters.reactable import ReactableExporter

        # Load JavaScript dependencies for sparkline visualization from file
        deps_file = Path(__file__).parent.parent / "panels" / "templates" / "plotly_deps.js"
        with open(deps_file) as f:
            js_deps_content = f.read()

        js_deps = f"<script>\n{js_deps_content}\n</script>"

        # Display the JavaScript dependencies
        display(HTML(js_deps))  # type: ignore

        exporter = ReactableExporter()
        return exporter.export(self)

    def to_dataframe(self) -> pl.DataFrame:
        """Export processed DataFrame.

        Returns:
            Processed DataFrame
        """
        return self.data

    def to_rtf(self, filename: str, **kwargs: Any) -> None:
        """Export to RTF for regulatory submissions.

        Args:
            filename: Output filename
            **kwargs: Additional RTF options
        """
        return None

    def to_plotnine(self) -> Any:
        """Generate static plot using plotnine.

        Returns:
            ggplot object
        """
        return None

    def get_panel_by_type(self, panel_type: type[Panel]) -> list[Panel]:
        """Get all panels of a specific type.

        Args:
            panel_type: Type of panel to filter

        Returns:
            List of panels matching the type
        """
        return [p for p in self.panels if isinstance(p, panel_type)]

    def update_config(self, **kwargs: Any) -> None:
        """Update configuration with new values.

        Args:
            **kwargs: Configuration parameters to update
        """
        current_config = self.config.model_dump()
        current_config.update(kwargs)
        self.config = Config(**current_config)

    def get_used_columns(self) -> list[str]:
        """Get all column names used in panels in the order they appear.

        Returns:
            List of column names used in panel order
        """
        # Import here to avoid circular imports
        from ..panels.sparkline import SparklinePanel
        from ..panels.text import TextPanel

        used_columns = []
        seen = set()

        for panel in self.panels:
            panel_columns = []

            if isinstance(panel, TextPanel):
                # Add group_by columns first
                if panel.group_by:
                    panel_columns.extend(panel.group_by)

                # Then add variable columns
                if panel.variables:
                    panel_columns.extend(panel.variables)

            elif isinstance(panel, SparklinePanel):
                # For SparklinePanel, we need all the columns it uses
                # Add main variable columns
                if panel.variables:
                    panel_columns.extend(panel.variables)

                # Add lower bound columns
                if panel.lower:
                    panel_columns.extend(panel.lower)

                # Add upper bound columns
                if panel.upper:
                    panel_columns.extend(panel.upper)

                # Add reference line column if it's a column name
                if panel.reference_line and isinstance(panel.reference_line, str):
                    panel_columns.append(panel.reference_line)

            # Add panel columns to used_columns, avoiding duplicates
            for col in panel_columns:
                if col not in seen:
                    seen.add(col)
                    used_columns.append(col)

        return used_columns

    def get_prepared_data(self) -> pl.DataFrame:
        """Get data filtered to only used columns.

        Returns:
            DataFrame with only columns used in panels
        """
        used_columns = self.get_used_columns()
        return self.data.select(used_columns)

    def prepare_panels(self) -> None:
        """Prepare panels with data-specific configuration."""
        data = self.get_prepared_data()

        # Import here to avoid circular imports
        from ..panels.sparkline import SparklinePanel

        # Collect all SparklinePanel instances
        sparkline_panels = [p for p in self.panels if isinstance(p, SparklinePanel)]

        # Compute shared xlim for all sparkline panels (even if just one)
        if sparkline_panels:
            shared_xlim = SparklinePanel.compute_shared_xlim(sparkline_panels, data)
            # Apply shared xlim to all panels that don't have explicit xlim
            for sp_panel in sparkline_panels:
                if not sp_panel.xlim:
                    sp_panel.xlim = shared_xlim

        # Let each panel handle any other preparation
        for panel in self.panels:
            panel.prepare(data)

    def get_grouping_columns(self) -> list[str]:
        """Get grouping columns from panels.

        Returns:
            List of grouping column names
        """
        # Import here to avoid circular imports
        from ..panels.text import TextPanel

        for panel in self.panels:
            if isinstance(panel, TextPanel) and panel.group_by:
                return panel.group_by
        return []

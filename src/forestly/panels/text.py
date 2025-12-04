# pyre-strict
"""Text panel module for forest plot system."""

import polars as pl
from pydantic import Field, field_validator

from forestly.panels.base import Panel


class TextPanel(Panel):
    """Display one or more text/numeric columns."""

    group_by: list[str] = Field(default_factory=list, description="Columns to group by")
    align: str = Field(
        default="center", description="Alignment for columns: 'left', 'center', or 'right'"
    )

    @field_validator("group_by", "labels", "variables", mode="before")  # pyre-fixme[56]
    @classmethod
    def normalize_to_list(cls, v: str | list[str]) -> list[str]:
        """Normalize all string/list fields to list format."""
        if isinstance(v, str):
            return [v]
        return v if v else []

    @field_validator("align")  # pyre-fixme[56]
    @classmethod
    def validate_align(cls, v: str) -> str:
        """Validate alignment is one of allowed values."""
        allowed = ["left", "center", "right"]
        if v not in allowed:
            raise ValueError(f"align must be one of {allowed}, got '{v}'")
        return v

    def render(
        self, data: pl.DataFrame
    ) -> dict[
        str, str | list[str] | int | list[int] | pl.DataFrame | float | tuple[float, float] | None
    ]:
        """Render panel data for display.

        Args:
            data: Input DataFrame

        Returns:
            Rendered data dictionary
        """
        result: dict[
            str,
            str | list[str] | int | list[int] | pl.DataFrame | float | tuple[float, float] | None,
        ] = {"data": data}

        if self.variables:
            result["columns"] = self.variables

        if self.group_by:
            result["group_by"] = self.group_by

        if self.labels:
            result["labels"] = self.labels

        if self.width:
            widths = [self.width] if isinstance(self.width, int) else self.width
            result["widths"] = widths

        result["title"] = self.title
        result["footer"] = self.footer

        return result

    def get_required_columns(self) -> set[str]:
        """Get columns required by this panel.

        Returns:
            Set of required column names
        """
        required = set()

        if self.variables:
            required.update(self.variables)

        if self.group_by:
            required.update(self.group_by)

        return required

    def apply_grouping(self, data: pl.DataFrame) -> pl.DataFrame:
        """Apply hierarchical grouping to data.

        Args:
            data: Input DataFrame

        Returns:
            DataFrame with grouping applied
        """
        if not self.group_by:
            return data

        # Sort by group columns to ensure proper hierarchy
        return data.sort(self.group_by)

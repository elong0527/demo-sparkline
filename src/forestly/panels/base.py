# pyre-strict
"""Base panel module for forest plot system."""

from abc import ABC, abstractmethod

import polars as pl
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Panel(BaseModel, ABC):
    """Base class for display panels."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    variables: list[str] = Field(default_factory=list, description="Panel variables/columns")
    title: str | None = Field(default=None, description="Panel title")
    labels: list[str] = Field(default_factory=list, description="Labels for display")
    width: int | list[int] | None = Field(default=None, description="Width configuration")
    footer: str = Field(default="", description="Panel footer text")

    @field_validator("labels", "variables", mode="before")  # pyre-fixme[56]
    @classmethod
    def normalize_to_list(cls, v: str | list[str]) -> list[str]:
        """Normalize all string/list fields to list format."""
        if isinstance(v, str):
            return [v]
        return v if v else []

    @abstractmethod
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
        pass

    @abstractmethod
    def get_required_columns(self) -> set[str]:
        """Get columns required by this panel.

        Returns:
            Set of required column names
        """
        pass

    def validate_columns(self, data: pl.DataFrame) -> None:
        """Validate that required columns exist in data.

        Args:
            data: Input DataFrame

        Raises:
            ValueError: If required columns are missing
        """
        required = self.get_required_columns()
        available = set(data.columns)
        missing = required - available

        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    def prepare(self, data: pl.DataFrame) -> None:
        """Prepare panel with data-specific configuration.

        Args:
            data: Input DataFrame

        Note:
            Override this method in subclasses to implement panel-specific
            preparation logic (e.g., inferring xlim for SparklinePanel).
        """
        pass

    def get_width_list(self, count: int) -> list[int | None]:
        """Get normalized width list matching the count.

        Args:
            count: Expected number of width values

        Returns:
            List of width values or None values
        """
        if self.width is None:
            # pyre-ignore[7]: List[int] is compatible with List[Optional[int]]
            return [None] * count
        if isinstance(self.width, int):
            # pyre-ignore[7]: List[int] is compatible with List[Optional[int]]
            return [self.width] * count
        # Ensure list has correct length
        result: list[int | None] = list(self.width)
        if len(result) < count:
            result.extend([None] * (count - len(result)))
        return result[:count]

    def get_color_list(
        self, colors: list[str] | None, count: int, default: str = "#4A90E2"
    ) -> list[str]:
        """Get color list with fallback to default for missing colors.

        Args:
            colors: Optional list of color strings
            count: Number of colors needed
            default: Default color to use when colors list is insufficient

        Returns:
            List of color strings with exactly 'count' elements
        """
        if not colors:
            return [default] * count

        result = []
        for i in range(count):
            if i < len(colors):
                result.append(colors[i])
            else:
                result.append(default)
        return result

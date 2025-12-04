# pyre-strict
"""Configuration module for forest plot system."""

from collections.abc import Callable

from pydantic import BaseModel, ConfigDict, Field


class Config(BaseModel):
    """Configuration for forest plot display and documentation."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    figure_width: float | None = None
    figure_height: float | None = None
    sparkline_height: int = Field(default=30, gt=0)
    font_size: int = Field(default=12, gt=0)  # Font size for text and legends

    colors: list[str] | None = None
    reference_line_color: str = "#00000050"

    formatters: dict[str, Callable[..., str]] | None = None

    title: str | None = None
    footnote: str | None = None
    source: str | None = None

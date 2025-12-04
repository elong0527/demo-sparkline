# pyre-strict
import unittest
from typing import Any
from unittest.mock import MagicMock, patch

import polars as pl

from forestly.core.config import Config
from forestly.core.forest_plot import ForestPlot
from forestly.exporters.reactable import ReactableExporter
from forestly.panels.sparkline import SparklinePanel
from forestly.panels.text import TextPanel


class TestReactableExporter(unittest.TestCase):
    def setUp(self) -> None:
        self.exporter = ReactableExporter()
        self.data = pl.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
        self.config = Config()

    def test_create_text_columns_with_group(self) -> None:
        # Case 1: Simple variable
        panel = TextPanel(variables=["col1"])
        columns, group = self.exporter._create_text_columns_with_group(panel, self.config)
        self.assertEqual(len(columns), 1)
        self.assertEqual(columns[0].id, "col1")
        self.assertIsNone(group)

        # Case 2: Grouping
        panel = TextPanel(variables=["col1"], group_by=["col2"])
        columns, group = self.exporter._create_text_columns_with_group(panel, self.config)
        # Should have 2 columns: group col and var col
        self.assertEqual(len(columns), 2)
        self.assertEqual(columns[0].id, "col2")
        self.assertEqual(columns[1].id, "col1")

        # Case 3: Title and multiple variables -> Column Group
        panel = TextPanel(variables=["col1", "col2"], title="Group Title")
        columns, group = self.exporter._create_text_columns_with_group(panel, self.config)
        self.assertEqual(len(columns), 2)
        self.assertIsNotNone(group)
        # pyre-ignore[16]: group is not None
        self.assertEqual(group.name, "Group Title")  # type: ignore
        self.assertEqual(group.columns, ["col1", "col2"])  # type: ignore

    def test_create_sparkline_columns(self) -> None:
        panel = SparklinePanel(variables=["col1"], lower=["col1"], upper=["col1"])
        # Mock generate_javascript to avoid file reading issues if templates missing in test env
        # But we want to test integration if possible. Assuming templates exist.
        # If not, we can patch generate_javascript.

        with patch.object(
            SparklinePanel, "generate_javascript", return_value="console.log('test')"
        ) as mock_js:
            columns = self.exporter._create_sparkline_columns(panel, self.config)

            self.assertEqual(len(columns), 1)
            self.assertEqual(columns[0].id, "col1")
            # Should call generate_javascript
            mock_js.assert_called()

    def test_build_reactable(self) -> None:
        # Mock columns and groups
        columns: list[Any] = []
        column_groups: list[Any] = []
        group_by = ["col2"]

        # We need to mock Reactable class because it might not be fully functional in this env or we just want to check args
        with patch("forestly.exporters.reactable.Reactable") as MockReactable:
            self.exporter._build_reactable(self.data, columns, column_groups, group_by, self.config)

            # Check arguments passed to Reactable constructor
            call_args = MockReactable.call_args[1]
            self.assertTrue(call_args["data"].equals(self.data))
            self.assertEqual(call_args["group_by"], "col2")
            self.assertTrue(call_args["default_expanded"])

    def test_export(self) -> None:
        # Integration-like test for export method
        fp = MagicMock(spec=ForestPlot)
        fp.get_prepared_data.return_value = self.data
        fp.panels = [TextPanel(variables=["col1"])]
        fp.config = self.config
        fp.get_used_columns.return_value = ["col1"]
        fp.get_grouping_columns.return_value = []

        with patch("forestly.exporters.reactable.Reactable") as MockReactable:
            self.exporter.export(fp)

            fp.prepare_panels.assert_called_once()
            MockReactable.assert_called_once()


if __name__ == "__main__":
    unittest.main()

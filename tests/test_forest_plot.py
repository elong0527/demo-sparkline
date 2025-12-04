# pyre-strict
import unittest
from typing import Any

import polars as pl

from forestly.core.forest_plot import ForestPlot
from forestly.panels.base import Panel


# Mock Panel for testing
class MockPanel(Panel):
    def render(self, data: pl.DataFrame) -> dict[str, Any]:
        return {"type": "mock", "data": "rendered"}

    def get_required_columns(self) -> set[str]:
        return {"col1"}

    def prepare(self, data: pl.DataFrame) -> None:
        pass


class TestForestPlot(unittest.TestCase):
    def setUp(self) -> None:
        self.sample_data = pl.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
        self.mock_panel = MockPanel()

    def test_forest_plot_initialization(self) -> None:
        fp = ForestPlot(data=self.sample_data, panels=[self.mock_panel])
        self.assertIsInstance(fp, ForestPlot)
        self.assertTrue(fp.data.equals(self.sample_data))
        self.assertEqual(len(fp.panels), 1)

    def test_validate_data_empty(self) -> None:
        empty_data = pl.DataFrame()
        with self.assertRaisesRegex(ValueError, "Data cannot be empty"):
            ForestPlot(data=empty_data, panels=[self.mock_panel])

    def test_validate_panels_empty(self) -> None:
        with self.assertRaisesRegex(ValueError, "At least one panel must be provided"):
            ForestPlot(data=self.sample_data, panels=[])

    def test_validate_columns_missing(self) -> None:
        # MockPanel requires "col1", but we provide data without it
        bad_data = pl.DataFrame({"col2": ["a", "b", "c"]})
        with self.assertRaisesRegex(ValueError, "Missing required columns in data"):
            ForestPlot(data=bad_data, panels=[self.mock_panel])

    def test_prepare_reactable_data(self) -> None:
        fp = ForestPlot(data=self.sample_data, panels=[self.mock_panel])
        result = fp._prepare_reactable_data()

        self.assertIn("data", result)
        self.assertIn("panels", result)
        self.assertIn("config", result)
        self.assertTrue(result["data"].equals(self.sample_data))
        self.assertEqual(len(result["panels"]), 1)
        self.assertEqual(result["panels"][0], {"type": "mock", "data": "rendered"})

    def test_update_config(self) -> None:
        fp = ForestPlot(data=self.sample_data, panels=[self.mock_panel])
        self.assertIsNone(fp.config.figure_width)

        fp.update_config(figure_width=100.0)
        self.assertEqual(fp.config.figure_width, 100.0)

    def test_to_dataframe(self) -> None:
        fp = ForestPlot(data=self.sample_data, panels=[self.mock_panel])
        self.assertTrue(fp.to_dataframe().equals(self.sample_data))

    def test_to_rtf(self) -> None:
        fp = ForestPlot(data=self.sample_data, panels=[self.mock_panel])
        # Currently returns None
        fp.to_rtf("test.rtf")

    def test_to_plotnine(self) -> None:
        fp = ForestPlot(data=self.sample_data, panels=[self.mock_panel])
        # Currently returns None
        self.assertIsNone(fp.to_plotnine())

    def test_get_panel_by_type(self) -> None:
        fp = ForestPlot(data=self.sample_data, panels=[self.mock_panel])
        panels = fp.get_panel_by_type(MockPanel)
        self.assertEqual(len(panels), 1)
        self.assertIsInstance(panels[0], MockPanel)

        # Test with different type
        from forestly.panels.text import TextPanel

        panels = fp.get_panel_by_type(TextPanel)
        self.assertEqual(len(panels), 0)

    def test_get_used_columns(self) -> None:
        # MockPanel requires "col1"
        ForestPlot(data=self.sample_data, panels=[self.mock_panel])

        # MockPanel doesn't implement logic to return columns in get_used_columns via inspection
        # But ForestPlot.get_used_columns calls panel.get_required_columns indirectly via logic?
        # Actually ForestPlot.get_used_columns checks specific panel types (TextPanel, SparklinePanel).
        # MockPanel is neither, so it might return empty list unless we add logic or use real panels.

        # Let's use real panels for this test
        from forestly.panels.text import TextPanel

        text_panel = TextPanel(variables=["col1"], group_by=["col2"])
        fp_text = ForestPlot(data=self.sample_data, panels=[text_panel])

        used = fp_text.get_used_columns()
        # Order: group_by, variables
        self.assertEqual(used, ["col2", "col1"])

    def test_prepare_panels(self) -> None:
        # Test that prepare is called on panels
        # We can mock the prepare method of MockPanel
        # But MockPanel.prepare is already defined as pass.
        # Let's verify it runs without error first.
        fp = ForestPlot(data=self.sample_data, panels=[self.mock_panel])
        fp.prepare_panels()

        # Test SparklinePanel shared xlim logic
        from forestly.panels.sparkline import SparklinePanel

        data = pl.DataFrame({"est": [1.0, 2.0], "low": [0.5, 1.5], "high": [1.5, 2.5]})
        sp1 = SparklinePanel(variables=["est"], lower=["low"], upper=["high"])
        sp2 = SparklinePanel(variables=["est"], lower=["low"], upper=["high"])

        fp_sp = ForestPlot(data=data, panels=[sp1, sp2])
        fp_sp.prepare_panels()

        # Check that xlim was set and is shared
        self.assertIsNotNone(sp1.xlim)
        self.assertIsNotNone(sp2.xlim)
        self.assertEqual(sp1.xlim, sp2.xlim)

    def test_get_grouping_columns(self) -> None:
        from forestly.panels.text import TextPanel

        text_panel = TextPanel(variables=["col1"], group_by=["col2"])
        fp = ForestPlot(data=self.sample_data, panels=[text_panel])

        self.assertEqual(fp.get_grouping_columns(), ["col2"])

        # No grouping
        fp_none = ForestPlot(data=self.sample_data, panels=[self.mock_panel])
        self.assertEqual(fp_none.get_grouping_columns(), [])


if __name__ == "__main__":
    unittest.main()

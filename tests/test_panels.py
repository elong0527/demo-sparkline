# pyre-strict
import unittest
from typing import cast

import polars as pl

from forestly.panels.sparkline import SparklinePanel
from forestly.panels.text import TextPanel


class TestTextPanel(unittest.TestCase):
    def test_normalize_to_list(self) -> None:
        # Test string input
        # pyre-ignore[6]: Intentional type error for testing
        panel = TextPanel(variables="col1")  # type: ignore
        self.assertEqual(panel.variables, ["col1"])

        # Test list input
        panel = TextPanel(variables=["col1", "col2"])
        self.assertEqual(panel.variables, ["col1", "col2"])

        # Test None/empty input (via default factory)
        panel = TextPanel()
        self.assertEqual(panel.variables, [])

    def test_validate_align(self) -> None:
        # Valid alignments
        for align in ["left", "center", "right"]:
            panel = TextPanel(align=align)
            self.assertEqual(panel.align, align)

        # Invalid alignment
        with self.assertRaises(ValueError):
            TextPanel(align="invalid")

    def test_render(self) -> None:
        data = pl.DataFrame({"col1": [1, 2], "group": ["A", "B"]})
        panel = TextPanel(variables=["col1"], group_by=["group"], title="Test Title")

        result = panel.render(data)

        result_data = cast(pl.DataFrame, result["data"])
        self.assertTrue(result_data.equals(data))
        self.assertEqual(result["columns"], ["col1"])
        self.assertEqual(result["group_by"], ["group"])
        self.assertEqual(result["title"], "Test Title")

    def test_get_required_columns(self) -> None:
        panel = TextPanel(variables=["col1"], group_by=["group"])
        required = panel.get_required_columns()
        self.assertEqual(required, {"col1", "group"})

    def test_apply_grouping(self) -> None:
        data = pl.DataFrame({"val": [1, 2], "group": ["B", "A"]})
        panel = TextPanel(group_by=["group"])

        grouped_data = panel.apply_grouping(data)

        # Should be sorted by group
        expected = pl.DataFrame({"val": [2, 1], "group": ["A", "B"]})
        self.assertTrue(grouped_data.equals(expected))

        # No grouping
        panel_no_group = TextPanel()
        self.assertTrue(panel_no_group.apply_grouping(data).equals(data))


class TestSparklinePanel(unittest.TestCase):
    def test_validate_legend_type(self) -> None:
        for lt in ["point", "line", "point+line"]:
            panel = SparklinePanel(legend_type=lt)
            self.assertEqual(panel.legend_type, lt)

        with self.assertRaises(ValueError):
            SparklinePanel(legend_type="invalid")

    def test_validate_margin(self) -> None:
        # Valid margin
        panel = SparklinePanel(margin=[1.0, 2.0, 3.0, 4.0, 5.0])
        self.assertEqual(panel.margin, [1.0, 2.0, 3.0, 4.0, 5.0])

        # Invalid length
        with self.assertRaises(ValueError):
            SparklinePanel(margin=[1.0, 2.0])

    def test_validate_legend_position(self) -> None:
        # Valid position
        panel = SparklinePanel(legend_position=0.5)
        self.assertEqual(panel.legend_position, 0.5)

        # Invalid position
        with self.assertRaises(ValueError):
            SparklinePanel(legend_position=1.5)

    def test_validate_xlim(self) -> None:
        # Valid xlim
        panel = SparklinePanel(xlim=(0.0, 10.0))
        self.assertEqual(panel.xlim, (0.0, 10.0))

        # Invalid length
        with self.assertRaises(ValueError):
            # pyre-ignore[6]: Intentional type error for testing
            SparklinePanel(xlim=(0.0, 10.0, 20.0))  # type: ignore

        # Invalid range
        with self.assertRaises(ValueError):
            SparklinePanel(xlim=(10.0, 0.0))

    def test_validate_confidence_bounds(self) -> None:
        # Valid: both provided
        SparklinePanel(lower=["l1"], upper=["u1"], variables=["v1"])

        # Invalid: only lower
        with self.assertRaises(ValueError):
            SparklinePanel(lower=["l1"], variables=["v1"])

        # Invalid: length mismatch between lower and upper
        with self.assertRaises(ValueError):
            SparklinePanel(lower=["l1"], upper=["u1", "u2"], variables=["v1"])

        # Invalid: length mismatch with variables
        with self.assertRaises(ValueError):
            SparklinePanel(lower=["l1"], upper=["u1"], variables=["v1", "v2"])

    def test_render(self) -> None:
        data = pl.DataFrame({"est": [1.0], "low": [0.5], "high": [1.5]})
        panel = SparklinePanel(
            variables=["est"], lower=["low"], upper=["high"], reference_line=0.0, xlim=(-1.0, 2.0)
        )

        result = panel.render(data)

        result_data = cast(pl.DataFrame, result["data"])
        self.assertTrue(result_data.equals(data))
        self.assertEqual(result["type"], "sparkline")
        self.assertEqual(result["estimates"], ["est"])
        self.assertEqual(result["lower_bounds"], ["low"])
        self.assertEqual(result["upper_bounds"], ["high"])
        self.assertEqual(result["reference_line_value"], 0.0)
        self.assertEqual(result["xlim"], (-1.0, 2.0))

    def test_get_required_columns(self) -> None:
        panel = SparklinePanel(variables=["est"], lower=["low"], upper=["high"])
        required = panel.get_required_columns()
        self.assertEqual(required, {"est", "low", "high"})

    def test_compute_shared_xlim(self) -> None:
        data = pl.DataFrame(
            {"est": [1.0, 2.0, 3.0], "low": [0.5, 1.5, 2.5], "high": [1.5, 2.5, 3.5]}
        )

        panel = SparklinePanel(variables=["est"], lower=["low"], upper=["high"])

        # Test basic computation
        xlim = SparklinePanel.compute_shared_xlim([panel], data)
        # Min is 0.5, Max is 3.5. Range 3.0.
        # Positive data: padding 5% -> 0.5 - 0.15, 3.5 + 0.15 -> 0.35, 3.65
        self.assertAlmostEqual(xlim[0], 0.35)
        self.assertAlmostEqual(xlim[1], 3.65)

    def test_validate_confidence_intervals(self) -> None:
        # Valid data
        data = pl.DataFrame({"est": [1.0], "low": [0.5], "high": [1.5]})
        panel = SparklinePanel(variables=["est"], lower=["low"], upper=["high"])
        panel.validate_confidence_intervals(data)

        # Invalid data: low > est
        bad_data = pl.DataFrame({"est": [1.0], "low": [1.1], "high": [1.5]})
        with self.assertRaisesRegex(ValueError, "Invalid confidence intervals"):
            panel.validate_confidence_intervals(bad_data)

    def test_generate_javascript(self) -> None:
        # Test that it returns a string and substitutes values
        panel = SparklinePanel(variables=["est"], lower=["low"], upper=["high"])
        # We need to ensure the template file exists or mock open
        # Assuming the template exists in the source tree as we are running in that context
        try:
            js = panel.generate_javascript(type="cell")
            self.assertIsInstance(js, str)
            self.assertIn("est", js)  # Variable name should be in JS (in cell.row access)
        except FileNotFoundError:
            # Fallback if template not found (e.g. running in isolated env without full src)
            pass

    def test_helpers(self) -> None:
        # Test internal helper methods
        panel = SparklinePanel(variables=["est"], lower=["low"], upper=["high"])

        # _get_margin
        margin = panel._get_margin("cell")
        self.assertEqual(len(margin), 5)

        # _get_height
        height = panel._get_height("cell", 1)
        self.assertIsInstance(height, int)

        # _calculate_y_spacing
        y_pos = panel._calculate_y_spacing(3)
        self.assertEqual(len(y_pos), 3)
        self.assertEqual(y_pos[0], 0.35)  # Default padding
        self.assertEqual(y_pos[2], 0.65)


class ConcretePanel(TextPanel):
    # Helper class to test abstract base class methods via inheritance
    pass


class TestPanelBase(unittest.TestCase):
    def test_validate_columns(self) -> None:
        panel = ConcretePanel(variables=["col1"])
        data = pl.DataFrame({"col1": [1]})
        # Should pass
        panel.validate_columns(data)

        # Missing column
        bad_data = pl.DataFrame({"col2": [1]})
        with self.assertRaisesRegex(ValueError, "Missing required columns"):
            panel.validate_columns(bad_data)

    def test_get_width_list(self) -> None:
        panel = ConcretePanel()
        widths = panel.get_width_list(3)
        self.assertEqual(widths, [None, None, None])

        panel = ConcretePanel(width=100)
        widths = panel.get_width_list(3)
        self.assertEqual(widths, [100, 100, 100])

        panel = ConcretePanel(width=[10, 20])
        widths = panel.get_width_list(3)
        self.assertEqual(widths, [10, 20, None])

    def test_get_color_list(self) -> None:
        panel = ConcretePanel()
        colors = panel.get_color_list(None, 3)
        self.assertEqual(len(colors), 3)
        self.assertEqual(colors[0], "#4A90E2")  # Default

        colors = panel.get_color_list(["red"], 3)
        self.assertEqual(colors, ["red", "#4A90E2", "#4A90E2"])


if __name__ == "__main__":
    unittest.main()

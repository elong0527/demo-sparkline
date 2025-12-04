
import pytest
import polars as pl
from forestly.core.forest_plot import ForestPlot
from forestly.core.config import Config
from forestly.panels.base import Panel
from typing import List, Set, Any

# Mock Panel for testing
class MockPanel(Panel):
    def render(self, data: pl.DataFrame) -> dict:
        return {"type": "mock", "data": "rendered"}

    def get_required_columns(self) -> Set[str]:
        return {"col1"}
        
    def prepare(self, data: pl.DataFrame) -> None:
        pass

@pytest.fixture
def sample_data():
    return pl.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})

@pytest.fixture
def mock_panel():
    return MockPanel()

def test_forest_plot_initialization(sample_data, mock_panel):
    fp = ForestPlot(data=sample_data, panels=[mock_panel])
    assert isinstance(fp, ForestPlot)
    assert fp.data.equals(sample_data)
    assert len(fp.panels) == 1

def test_validate_data_empty(mock_panel):
    empty_data = pl.DataFrame()
    with pytest.raises(ValueError, match="Data cannot be empty"):
        ForestPlot(data=empty_data, panels=[mock_panel])

def test_validate_panels_empty(sample_data):
    with pytest.raises(ValueError, match="At least one panel must be provided"):
        ForestPlot(data=sample_data, panels=[])

def test_validate_columns_missing(mock_panel):
    # MockPanel requires "col1", but we provide data without it
    bad_data = pl.DataFrame({"col2": ["a", "b", "c"]})
    with pytest.raises(ValueError, match="Missing required columns in data"):
        ForestPlot(data=bad_data, panels=[mock_panel])

def test_prepare_reactable_data(sample_data, mock_panel):
    fp = ForestPlot(data=sample_data, panels=[mock_panel])
    result = fp._prepare_reactable_data()
    
    assert "data" in result
    assert "panels" in result
    assert "config" in result
    assert result["data"].equals(sample_data)
    assert len(result["panels"]) == 1
    assert result["panels"][0] == {"type": "mock", "data": "rendered"}

def test_update_config(sample_data, mock_panel):
    fp = ForestPlot(data=sample_data, panels=[mock_panel])
    assert fp.config.figure_width is None
    
    fp.update_config(figure_width=100.0)
    assert fp.config.figure_width == 100.0

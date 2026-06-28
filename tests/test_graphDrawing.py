import sys
from unittest.mock import MagicMock

# matplotlib is not installed in the test environment; mock before import
sys.modules.setdefault('matplotlib', MagicMock())
sys.modules.setdefault('matplotlib.pyplot', MagicMock())

import graphDrawing  # noqa: E402


class TestRedraw:
    def test_normal_single_file(self, mocker, tmp_path):
        """1ファイルで redraw を呼び出す"""
        csv_file = tmp_path / "front.csv"
        csv_file.write_text("index,f1,f2\n0,0.1,0.9\n1,0.5,0.5\n")

        mock_scatter = mocker.patch('graphDrawing.plt.scatter')
        mocker.patch('graphDrawing.plt.grid')
        mocker.patch('graphDrawing.plt.xlabel')
        mocker.patch('graphDrawing.plt.ylabel')
        mocker.patch('graphDrawing.plt.legend')
        mocker.patch('graphDrawing.plt.show')

        graphDrawing.redraw([str(csv_file)])

        mock_scatter.assert_called_once()
        assert mock_scatter.call_args[1]['c'] == graphDrawing.colors[0]
        assert mock_scatter.call_args[1]['marker'] == graphDrawing.markers[0]

    def test_normal_multiple_files(self, mocker, tmp_path):
        """複数ファイルで scatter が複数回呼び出される"""
        csv_file1 = tmp_path / "front1.csv"
        csv_file1.write_text("index,f1,f2\n0,0.1,0.9\n")
        csv_file2 = tmp_path / "front2.csv"
        csv_file2.write_text("index,f1,f2\n0,0.2,0.8\n")

        mock_scatter = mocker.patch('graphDrawing.plt.scatter')
        mocker.patch('graphDrawing.plt.grid')
        mocker.patch('graphDrawing.plt.xlabel')
        mocker.patch('graphDrawing.plt.ylabel')
        mocker.patch('graphDrawing.plt.legend')
        mocker.patch('graphDrawing.plt.show')

        graphDrawing.redraw([str(csv_file1), str(csv_file2)])

        assert mock_scatter.call_count == 2

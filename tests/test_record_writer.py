import datetime
import numpy as np
import logger
import record_writer


class TestWrite4plot:
    def setup_method(self):
        logger.reset_log()
        logger.LOG_FIT.append(np.array([[0.0, 1.0], [1.0, 0.0]]))

    def test_normal_returns_path(self, mocker):
        mocker.patch('os.makedirs')
        mocker.patch('pandas.DataFrame.to_csv')
        s_time = datetime.datetime(2024, 1, 1, 12, 0, 0)
        result = record_writer.write4plot(
            trial=1, nums=('1', '1'), f_name='ZDT2',
            m_name='MOPSO', s_time=s_time
        )
        assert isinstance(result, str)
        assert '1_MOPSO' in result

    def test_normal_creates_directory(self, mocker):
        mock_makedirs = mocker.patch('os.makedirs')
        mocker.patch('pandas.DataFrame.to_csv')
        s_time = datetime.datetime(2024, 1, 1, 12, 0, 0)
        record_writer.write4plot(
            trial=1, nums=('1', '1'), f_name='ZDT2',
            m_name='MOPSO', s_time=s_time
        )
        mock_makedirs.assert_called_once()

    def test_normal_dtlz1_columns(self, mocker):
        logger.reset_log()
        logger.LOG_FIT.append(np.array([[0.0, 0.5, 1.0], [1.0, 0.5, 0.0], [0.5, 0.0, 0.5]]))
        mocker.patch('os.makedirs')
        mocker.patch('pandas.DataFrame.to_csv')
        s_time = datetime.datetime(2024, 1, 1, 12, 0, 0)
        result = record_writer.write4plot(
            trial=1, nums=('3', '1'), f_name='DTLZ1',
            m_name='SENIOR', s_time=s_time
        )
        assert isinstance(result, str)


class TestWriteRecord:
    def test_normal(self, mocker):
        mock_cell = mocker.Mock()
        mock_cell.value = None
        mock_ws = mocker.Mock()
        mock_ws.cell.return_value = mock_cell
        mock_wb = mocker.Mock()
        mock_wb.__getitem__ = mocker.Mock(return_value=mock_ws)
        mocker.patch('openpyxl.load_workbook', return_value=mock_wb)

        record_writer.write_record(
            'dummy.xlsx', 100,
            datetime.datetime(2024, 1, 1, 12, 0, 0),
            ('ZDT2', 'MOPSO', 'None'),
            'test comment', 1.23, 0,
            np.array([0.5, 0.6, 0.7]),
            np.array([0.8, 0.9, 1.0]),
        )
        mock_wb.save.assert_called_once_with('dummy.xlsx')

    def test_normal_finds_empty_row(self, mocker):
        # 1行目に値あり → r += 1 (line 38) を通過し、2行目の None でbreak
        row1_cell = mocker.Mock()
        row1_cell.value = "existing_data"
        row2_cell = mocker.Mock()
        row2_cell.value = None

        call_count = [0]

        def cell_side_effect(row, column):
            call_count[0] += 1
            if row == 1 and column == 1:
                return row1_cell
            return row2_cell

        mock_ws = mocker.Mock()
        mock_ws.cell.side_effect = cell_side_effect
        mock_wb = mocker.Mock()
        mock_wb.__getitem__ = mocker.Mock(return_value=mock_ws)
        mocker.patch('openpyxl.load_workbook', return_value=mock_wb)

        record_writer.write_record(
            'dummy.xlsx', 100,
            datetime.datetime(2024, 1, 1, 12, 0, 0),
            ('ZDT2', 'MOPSO', 'None'),
            'test comment', 1.23, 0,
            np.array([0.5]),
        )
        mock_wb.save.assert_called_once_with('dummy.xlsx')

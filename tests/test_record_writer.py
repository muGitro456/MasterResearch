import datetime
import numpy as np
from src import logger
from src import record_writer


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

    def test_normal_default_output_dir_is_backlog(self, mocker):
        mocker.patch('os.makedirs')
        mocker.patch('pandas.DataFrame.to_csv')
        s_time = datetime.datetime(2024, 1, 1, 12, 0, 0)
        result = record_writer.write4plot(
            trial=1, nums=('1', '1'), f_name='ZDT2',
            m_name='MOPSO', s_time=s_time
        )
        assert result.startswith('backLog/')

    def test_normal_custom_output_dir_is_honored(self, mocker):
        mocker.patch('os.makedirs')
        mocker.patch('pandas.DataFrame.to_csv')
        s_time = datetime.datetime(2024, 1, 1, 12, 0, 0)
        result = record_writer.write4plot(
            trial=1, nums=('1', '1'), f_name='ZDT2',
            m_name='MOPSO', s_time=s_time, output_dir='custom_dir'
        )
        assert result.startswith('custom_dir/')
        assert 'backLog' not in result


class TestWriteRecord:
    def test_normal_creates_file_with_header(self, mocker, tmp_path):
        csv_path = str(tmp_path / 'record.csv')
        record_writer.write_record(
            csv_path, 100,
            datetime.datetime(2024, 1, 1, 12, 0, 0),
            ('ZDT2', 'MOPSO', 'None'),
            'test comment', 1.23, 0,
            np.array([0.5, 0.6, 0.7]),
        )
        import pandas as pd
        df = pd.read_csv(csv_path)
        assert len(df) == 1
        assert 'func_name' in df.columns
        assert df['func_name'].iloc[0] == 'ZDT2'

    def test_normal_appends_row_when_file_exists(self, mocker, tmp_path):
        csv_path = str(tmp_path / 'record.csv')
        args = (
            100,
            datetime.datetime(2024, 1, 1, 12, 0, 0),
            ('ZDT2', 'MOPSO', 'None'),
            'test', 1.0, 0,
            np.array([0.5]),
        )
        record_writer.write_record(csv_path, *args)
        record_writer.write_record(csv_path, *args)

        import pandas as pd
        df = pd.read_csv(csv_path)
        assert len(df) == 2

    def test_normal_creates_missing_parent_directory(self, tmp_path):
        csv_path = str(tmp_path / 'nested' / 'dir' / 'record.csv')
        record_writer.write_record(
            csv_path, 1,
            datetime.datetime(2024, 1, 1, 12, 0, 0),
            ('ZDT2', 'MOPSO', 'None'),
            'test', 1.0, 0,
            np.array([0.5]),
        )
        import pandas as pd
        df = pd.read_csv(csv_path)
        assert len(df) == 1

    def test_normal_writes_indicator_stats(self, tmp_path):
        csv_path = str(tmp_path / 'record.csv')
        indicator = np.array([0.5, 0.8, 0.3])
        record_writer.write_record(
            csv_path, 10,
            datetime.datetime(2024, 6, 1, 0, 0, 0),
            ('ZDT1', 'SENIOR', 'Ring_5'),
            '', 2.0, 50,
            indicator,
        )
        import pandas as pd
        df = pd.read_csv(csv_path)
        assert df['ind0_avg'].iloc[0] == pytest.approx(np.average(indicator))
        assert df['ind0_max'].iloc[0] == pytest.approx(np.max(indicator))
        assert df['ind0_argmax'].iloc[0] == f'No.{np.argmax(indicator) + 1}'


import pytest


class TestWriteTrajectory:
    def setup_method(self):
        logger.reset_log()

    def test_normal_creates_csv(self, tmp_path, mocker):
        mocker.patch('src.record_writer.logger.LOG_TRAJ', [
            np.array([[0.1, 0.9], [0.5, 0.5]]),
            np.array([[0.08, 0.92]]),
        ])
        record_writer.write_trajectory(str(tmp_path) + '/', 'ZDT2')
        csv_path = tmp_path / 'trajectory_best.csv'
        assert csv_path.exists()
        import pandas as pd
        df = pd.read_csv(csv_path)
        assert list(df.columns) == ['generation', 'point_idx', 'f1', 'f2']
        assert len(df) == 3  # 世代0:2点 + 世代1:1点

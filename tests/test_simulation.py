import numpy as np
from src import simulation


class TestFileIsLocked:
    def test_normal_file_not_locked(self, tmp_path):
        f = tmp_path / "test.csv"
        f.write_bytes(b"")
        assert simulation.file_is_locked(str(f)) is False

    def test_normal_file_is_locked(self, mocker, tmp_path):
        f = tmp_path / "dummy.csv"
        f.write_bytes(b"")
        mocker.patch('builtins.open', side_effect=OSError("locked"))
        assert simulation.file_is_locked(str(f)) is True

    def test_normal_missing_parent_directory_is_not_locked(self, tmp_path):
        """A non-existent parent dir is not a lock — file_is_locked is a pure
        check and must not create directories as a side effect (that is
        write_record's job, at the point it actually writes)."""
        target = tmp_path / "nested" / "dir" / "log.csv"
        assert simulation.file_is_locked(str(target)) is False
        assert not target.parent.exists()

    def test_normal_does_not_create_file_as_side_effect(self, tmp_path):
        """Checking a not-yet-existing path must not create it — file_is_locked
        is a pure check; write_record is responsible for actually creating
        the file when it writes."""
        target = tmp_path / "log.csv"
        assert simulation.file_is_locked(str(target)) is False
        assert not target.exists()

    def test_normal_empty_path_is_not_locked(self):
        """An empty path doesn't exist, so it's reported as not locked — the
        empty-string case itself is rejected earlier, at CLI argument
        parsing (see tests/test___main__.py)."""
        assert simulation.file_is_locked('') is False

    def test_normal_bare_filename_without_directory(self, tmp_path, monkeypatch):
        """A bare filename (no directory component) must still work."""
        monkeypatch.chdir(tmp_path)
        assert simulation.file_is_locked('log.csv') is False



class TestMain:
    def _make_mock_algo(self, mocker):
        mock_archive = mocker.Mock()
        mock_archive.fit_gb.shape = (3, 2)
        mock_archive.calc_cover_rate.return_value = 0.5
        mock_instance = mocker.Mock()
        mock_instance.simulation.return_value = mock_archive
        mock_class = mocker.Mock(return_value=mock_instance)
        return mock_class

    def test_normal_instruction_2char_meth1_no_C_flag(self, mocker):
        mock_class = self._make_mock_algo(mocker)
        mocker.patch('src.simulation.MOPSO', mock_class)
        mocker.patch('src.simulation.record_writer.write4plot', return_value='test_dir/')
        mocker.patch('src.simulation.metrics.evaluation')
        mocker.patch('src.simulation.record_writer.write_record')
        mocker.patch('src.simulation.record_writer.write_trajectory')

        simulation.run_simulation("19")  # comment/trial はデフォルト値

        mock_class.assert_called()

    def test_normal_instruction_2char_meth4_is_master_a(self, mocker):
        mock_class = self._make_mock_algo(mocker)
        mocker.patch('src.simulation.MASTER_A', mock_class)
        mocker.patch('src.simulation.record_writer.write4plot', return_value='test_dir/')
        mocker.patch('src.simulation.metrics.evaluation')
        mocker.patch('src.simulation.record_writer.write_record')
        mocker.patch('src.simulation.record_writer.write_trajectory')

        simulation.run_simulation("49")

        mock_class.assert_called()

    def test_normal_instruction_3char_with_comment_arg(self, mocker):
        mock_class = self._make_mock_algo(mocker)
        mocker.patch('src.simulation.MASTER_A', mock_class)
        mocker.patch('src.simulation.record_writer.write4plot', return_value='test_dir/')
        mocker.patch('src.simulation.metrics.evaluation')
        mocker.patch('src.simulation.record_writer.write_record')
        mocker.patch('src.simulation.record_writer.write_trajectory')

        simulation.run_simulation("491", comment='my_comment')

        mock_class.assert_called()

    def test_normal_instruction_3char_meth6_prints_subswarm(self, mocker, capsys):
        mock_class = self._make_mock_algo(mocker)
        mocker.patch('src.simulation.MASTER_C', mock_class)
        mocker.patch('src.simulation.record_writer.write4plot', return_value='test_dir/')
        mocker.patch('src.simulation.metrics.evaluation')
        mocker.patch('src.simulation.record_writer.write_record')
        mocker.patch('src.simulation.record_writer.write_trajectory')

        simulation.run_simulation("691")

        captured = capsys.readouterr()
        assert "N_SUBSWARM" in captured.out
        mock_class.assert_called()

    def test_normal_passes_output_dir_and_log_file_through(self, mocker):
        mock_class = self._make_mock_algo(mocker)
        mocker.patch('src.simulation.MOPSO', mock_class)
        mock_write4plot = mocker.patch('src.simulation.record_writer.write4plot', return_value='custom_dir/')
        mocker.patch('src.simulation.metrics.evaluation')
        mock_write_record = mocker.patch('src.simulation.record_writer.write_record')
        mocker.patch('src.simulation.record_writer.write_trajectory')

        simulation.run_simulation("19", output_dir='custom_dir', log_file='custom_log.csv')

        assert mock_write4plot.call_args.kwargs['output_dir'] == 'custom_dir'
        assert mock_write_record.call_args.args[0] == 'custom_log.csv'

    def test_normal_default_output_dir_and_log_file(self, mocker):
        mock_class = self._make_mock_algo(mocker)
        mocker.patch('src.simulation.MOPSO', mock_class)
        mock_write4plot = mocker.patch('src.simulation.record_writer.write4plot', return_value='backLog/')
        mocker.patch('src.simulation.metrics.evaluation')
        mock_write_record = mocker.patch('src.simulation.record_writer.write_record')
        mocker.patch('src.simulation.record_writer.write_trajectory')

        simulation.run_simulation("19")

        assert mock_write4plot.call_args.kwargs['output_dir'] == 'backLog'
        assert mock_write_record.call_args.args[0] == 'execution_log.csv'


class TestNotify:
    def test_normal_calls_notify_send(self, mocker):
        import src.__main__ as entry
        mock_run = mocker.patch('subprocess.run')
        entry._notify("テスト完了")
        mock_run.assert_called_once_with(
            ['notify-send', 'MasterResearch', 'テスト完了'],
            check=True, timeout=5
        )

    def test_normal_fallback_when_notify_send_missing(self, mocker, capsys):
        import src.__main__ as entry
        mocker.patch('subprocess.run', side_effect=FileNotFoundError)
        entry._notify("テスト完了")
        captured = capsys.readouterr()
        assert "テスト完了" in captured.out

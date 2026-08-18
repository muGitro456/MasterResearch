import numpy as np
from src import simulation


class TestFileIsLocked:
    def test_normal_file_not_locked(self, tmp_path):
        f = tmp_path / "test.csv"
        f.write_bytes(b"")
        assert simulation.file_is_locked(str(f)) is False

    def test_normal_file_is_locked(self, mocker):
        mocker.patch('builtins.open', side_effect=OSError("locked"))
        assert simulation.file_is_locked('dummy.csv') is True



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

        simulation.main("19")  # comment/trial はデフォルト値

        mock_class.assert_called()

    def test_normal_instruction_2char_meth4_is_master_a(self, mocker):
        mock_class = self._make_mock_algo(mocker)
        mocker.patch('src.simulation.MASTER_A', mock_class)
        mocker.patch('src.simulation.record_writer.write4plot', return_value='test_dir/')
        mocker.patch('src.simulation.metrics.evaluation')
        mocker.patch('src.simulation.record_writer.write_record')
        mocker.patch('src.simulation.record_writer.write_trajectory')

        simulation.main("49")

        mock_class.assert_called()

    def test_normal_instruction_3char_with_comment_arg(self, mocker):
        mock_class = self._make_mock_algo(mocker)
        mocker.patch('src.simulation.MASTER_A', mock_class)
        mocker.patch('src.simulation.record_writer.write4plot', return_value='test_dir/')
        mocker.patch('src.simulation.metrics.evaluation')
        mocker.patch('src.simulation.record_writer.write_record')
        mocker.patch('src.simulation.record_writer.write_trajectory')

        simulation.main("491", comment='my_comment')

        mock_class.assert_called()

    def test_normal_instruction_3char_meth6_prints_subswarm(self, mocker, capsys):
        mock_class = self._make_mock_algo(mocker)
        mocker.patch('src.simulation.MASTER_C', mock_class)
        mocker.patch('src.simulation.record_writer.write4plot', return_value='test_dir/')
        mocker.patch('src.simulation.metrics.evaluation')
        mocker.patch('src.simulation.record_writer.write_record')
        mocker.patch('src.simulation.record_writer.write_trajectory')

        simulation.main("691")

        captured = capsys.readouterr()
        assert "N_SUBSWARM" in captured.out
        mock_class.assert_called()


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

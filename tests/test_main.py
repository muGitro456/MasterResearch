import sys
from unittest.mock import MagicMock

sys.modules.setdefault('requests', MagicMock())

import numpy as np
import main


class TestFileIsLocked:
    def test_normal_file_not_locked(self, tmp_path):
        f = tmp_path / "test.csv"
        f.write_bytes(b"")
        assert main.file_is_locked(str(f)) is False

    def test_normal_file_is_locked(self, mocker):
        mocker.patch('builtins.open', side_effect=OSError("locked"))
        assert main.file_is_locked('dummy.csv') is True


class TestLineNotify:
    def test_normal_posts_to_line_api(self, mocker):
        mock_post = mocker.patch('main.requests.post')
        mocker.patch.dict('os.environ', {'LINE_NOTIFY_TOKEN': 'dummy_token'})
        main.line_notify("test message")
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == 'https://notify-api.line.me/api/notify'


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
        mocker.patch('main.MOPSO', mock_class)
        mocker.patch('main.record_writer.write4plot', return_value='test_dir/')
        mocker.patch('main.metrics.evaluation')
        mocker.patch('main.record_writer.write_record')
        mocker.patch('sys.argv', ['main.py'])

        main.main("19")

        mock_class.assert_called()

    def test_normal_instruction_2char_meth4_is_master_a(self, mocker):
        mock_class = self._make_mock_algo(mocker)
        mocker.patch('main.MASTER_A', mock_class)
        mocker.patch('main.record_writer.write4plot', return_value='test_dir/')
        mocker.patch('main.metrics.evaluation')
        mocker.patch('main.record_writer.write_record')
        mocker.patch('sys.argv', ['main.py'])

        main.main("49")

        mock_class.assert_called()

    def test_normal_instruction_3char_with_C_flag(self, mocker):
        mock_class = self._make_mock_algo(mocker)
        mocker.patch('main.MASTER_A', mock_class)
        mocker.patch('main.record_writer.write4plot', return_value='test_dir/')
        mocker.patch('main.metrics.evaluation')
        mocker.patch('main.record_writer.write_record')
        mocker.patch('sys.argv', ['main.py', '-C', 'my_comment'])

        main.main("491")

        mock_class.assert_called()

    def test_normal_instruction_3char_meth6_prints_subswarm(self, mocker, capsys):
        mock_class = self._make_mock_algo(mocker)
        mocker.patch('main.MASTER_C', mock_class)
        mocker.patch('main.record_writer.write4plot', return_value='test_dir/')
        mocker.patch('main.metrics.evaluation')
        mocker.patch('main.record_writer.write_record')
        mocker.patch('sys.argv', ['main.py'])

        main.main("691")

        captured = capsys.readouterr()
        assert "N_SUBSWARM" in captured.out
        mock_class.assert_called()

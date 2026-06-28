import sys
from unittest.mock import MagicMock

# requests is not installed in the test environment; mock before import
sys.modules.setdefault('requests', MagicMock())

import numpy as np  # noqa: E402
import pytest  # noqa: E402
import main  # noqa: E402


class TestXlsxIsOpen:
    def test_file_not_open(self, tmp_path):
        """書き込み可能なファイル → False を返す"""
        f = tmp_path / "test.xlsx"
        f.write_bytes(b"")
        assert main.xlsx_is_open(str(f)) is False

    def test_file_is_open(self, mocker):
        """open が例外を送出 → True を返す"""
        mocker.patch('builtins.open', side_effect=IOError("locked"))
        assert main.xlsx_is_open('dummy.xlsx') is True


class TestLineNotify:
    def test_posts_to_line_api(self, mocker):
        mock_post = mocker.patch('main.requests.post')
        mocker.patch.dict('os.environ', {'LINE_NOTIFY_TOKEN': 'dummy_token'})
        main.line_notify("test message")
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == 'https://notify-api.line.me/api/notify'


class TestMain:
    def _make_mock_algo(self, mocker):
        """アルゴリズムのモックを生成する"""
        mock_archive = mocker.Mock()
        mock_archive.fit_gb.shape = (3, 2)
        mock_archive.calc_cover_rate.return_value = 0.5
        mock_instance = mocker.Mock()
        mock_instance.simulation.return_value = mock_archive
        mock_class = mocker.Mock(return_value=mock_instance)
        return mock_class

    def test_instruction_2char_meth1_no_C_flag(self, mocker):
        """長さ2の命令(MOPSO, ZDT2), -C フラグなし"""
        mock_class = self._make_mock_algo(mocker)
        mocker.patch('main.MOPSO', mock_class)
        mocker.patch('main.record_writer.write4plot', return_value='test_dir/')
        mocker.patch('main.metrics.evaluation')
        mocker.patch('main.record_writer.write_record')
        mocker.patch('sys.argv', ['main.py'])

        main.main("19")

        mock_class.assert_called()

    def test_instruction_2char_meth4_is_master_a(self, mocker):
        """長さ2の命令でMETH_NUM='4' → TOPO_NUM='1', MASTER_A を使用"""
        mock_class = self._make_mock_algo(mocker)
        mocker.patch('main.MASTER_A', mock_class)
        mocker.patch('main.record_writer.write4plot', return_value='test_dir/')
        mocker.patch('main.metrics.evaluation')
        mocker.patch('main.record_writer.write_record')
        mocker.patch('sys.argv', ['main.py'])

        main.main("49")  # METH_NUM="4", FUNC_NUM="9"

        mock_class.assert_called()

    def test_instruction_3char_with_C_flag(self, mocker):
        """長さ3の命令(-C フラグあり), METH_NUM>3 (MASTER_A) パス"""
        mock_class = self._make_mock_algo(mocker)
        mocker.patch('main.MASTER_A', mock_class)
        mocker.patch('main.record_writer.write4plot', return_value='test_dir/')
        mocker.patch('main.metrics.evaluation')
        mocker.patch('main.record_writer.write_record')
        mocker.patch('sys.argv', ['main.py', '-C', 'my_comment'])

        main.main("491")  # METH_NUM="4", FUNC_NUM="9", TOPO_NUM="1"

        mock_class.assert_called()

    def test_instruction_3char_meth6_prints_subswarm(self, mocker, capsys):
        """METH_NUM='6' (MASTER_C) → N_SUBSWARM の print を通過する"""
        mock_class = self._make_mock_algo(mocker)
        mocker.patch('main.MASTER_C', mock_class)
        mocker.patch('main.record_writer.write4plot', return_value='test_dir/')
        mocker.patch('main.metrics.evaluation')
        mocker.patch('main.record_writer.write_record')
        mocker.patch('sys.argv', ['main.py'])

        main.main("691")  # METH_NUM="6", FUNC_NUM="9", TOPO_NUM="1"

        captured = capsys.readouterr()
        assert "N_SUBSWARM" in captured.out
        mock_class.assert_called()

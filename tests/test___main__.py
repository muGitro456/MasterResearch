"""Tests for src/__main__.py CLI entry point."""
import sys
from unittest.mock import patch
import src.__main__ as entry


_MOCK_METHODS = {
    '1': {'name': 'MOPSO'},
    '6': {'name': 'MASTER_C'},
}
_MOCK_FUNCTIONS = {'9': {'name': 'ZDT2'}}
_MOCK_TOPOLOGIES = {'0': {'name': 'なし'}, '1': {'name': 'Ring'}}


class TestSelectInteractive:
    def _patch_load(self, mocker):
        mocker.patch.object(entry, 'load_yaml', side_effect=lambda name: {
            'methods.yaml': _MOCK_METHODS,
            'functions.yaml': _MOCK_FUNCTIONS,
            'topologies.yaml': _MOCK_TOPOLOGIES,
        }[name])

    def test_non_master_method_returns_two_digit_instruction(self, mocker):
        self._patch_load(mocker)
        with patch('builtins.input', side_effect=['1', '9']):
            result = entry._select_interactive()
        assert result == ['19']

    def test_master_c_method_returns_three_digit_instruction(self, mocker):
        self._patch_load(mocker)
        with patch('builtins.input', side_effect=['6', '9', '1']):
            result = entry._select_interactive()
        assert result == ['691']

    def test_returns_list(self, mocker):
        self._patch_load(mocker)
        with patch('builtins.input', side_effect=['1', '9']):
            result = entry._select_interactive()
        assert isinstance(result, list)


class TestParseArgs:
    def test_defaults(self, mocker):
        mocker.patch('sys.argv', ['masterresearch'])
        args = entry._parse_args()
        assert args.manual is None
        assert args.trial == 100
        assert args.comment == 'ただのテスト'

    def test_manual_single(self, mocker):
        mocker.patch('sys.argv', ['masterresearch', '--manual', '691'])
        args = entry._parse_args()
        assert args.manual == ['691']

    def test_manual_multiple(self, mocker):
        mocker.patch('sys.argv', ['masterresearch', '--manual', '691', '27', '37'])
        args = entry._parse_args()
        assert args.manual == ['691', '27', '37']

    def test_trial_option(self, mocker):
        mocker.patch('sys.argv', ['masterresearch', '--trial', '5'])
        args = entry._parse_args()
        assert args.trial == 5

    def test_comment_long_option(self, mocker):
        mocker.patch('sys.argv', ['masterresearch', '--comment', 'my test'])
        args = entry._parse_args()
        assert args.comment == 'my test'

    def test_comment_short_option(self, mocker):
        mocker.patch('sys.argv', ['masterresearch', '-C', 'short'])
        args = entry._parse_args()
        assert args.comment == 'short'

    def test_combined_options(self, mocker):
        mocker.patch('sys.argv', ['masterresearch', '--manual', '691', '--trial', '1', '-C', 'CLIテスト'])
        args = entry._parse_args()
        assert args.manual == ['691']
        assert args.trial == 1
        assert args.comment == 'CLIテスト'


class TestCli:
    def test_manual_mode_dispatches_run_main(self, mocker):
        """--manual CODE calls run_main with correct args"""
        import src.__main__ as entry
        mock_run = mocker.patch.object(entry, 'run_main')
        mock_notify = mocker.patch.object(entry, '_notify')
        mocker.patch('sys.argv', ['masterresearch', '--manual', '691', '--trial', '1', '--comment', 'test'])
        entry.cli()
        mock_run.assert_called_once_with('691', trial=1, comment='test')
        mock_notify.assert_called_once()

    def test_manual_mode_multiple_codes(self, mocker):
        """--manual with multiple codes calls run_main for each"""
        import src.__main__ as entry
        mock_run = mocker.patch.object(entry, 'run_main')
        mocker.patch.object(entry, '_notify')
        mocker.patch('sys.argv', ['masterresearch', '--manual', '27', '37'])
        entry.cli()
        assert mock_run.call_count == 2

    def test_interactive_mode_routes_to_select(self, mocker):
        """No --manual flag calls _select_interactive"""
        import src.__main__ as entry
        mock_select = mocker.patch.object(entry, '_select_interactive', return_value=['691'])
        mock_run = mocker.patch.object(entry, 'run_main')
        mocker.patch.object(entry, '_notify')
        mocker.patch('sys.argv', ['masterresearch'])
        entry.cli()
        mock_select.assert_called_once()
        mock_run.assert_called_once_with('691', trial=100, comment='ただのテスト')

    def test_notify_called_after_all_runs(self, mocker):
        """_notify fires exactly once, after all instructions complete"""
        import src.__main__ as entry
        mocker.patch.object(entry, 'run_main')
        mock_notify = mocker.patch.object(entry, '_notify')
        mocker.patch('sys.argv', ['masterresearch', '--manual', '27', '37'])
        entry.cli()
        mock_notify.assert_called_once_with('プログラムの実行が完了しました')

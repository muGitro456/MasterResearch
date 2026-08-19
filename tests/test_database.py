import os
import runpy
import sys
import numpy as np

_DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'tools', 'database.py')


class TestDatabaseCLI:
    def _run(self, argv, mocker, extra_patches=None):
        mocker.patch.object(sys, 'argv', argv)
        if extra_patches:
            for target, kwargs in extra_patches.items():
                mocker.patch(target, **kwargs)
        runpy.run_path(_DATABASE_PATH, run_name='__main__')

    def test_normal_rni_first_better(self, mocker, capsys):
        mocker.patch.object(sys, 'argv', ['database.py', '--rni'])
        mocker.patch('builtins.input', side_effect=['f1.csv', 'f2.csv'])
        mocker.patch('metrics.rni', return_value=(0.7, 0.3))
        runpy.run_path(_DATABASE_PATH, run_name='__main__')
        captured = capsys.readouterr()
        assert "前者" in captured.out

    def test_normal_rni_second_better(self, mocker, capsys):
        mocker.patch.object(sys, 'argv', ['database.py', '--rni'])
        mocker.patch('builtins.input', side_effect=['f1.csv', 'f2.csv'])
        mocker.patch('metrics.rni', return_value=(0.3, 0.7))
        runpy.run_path(_DATABASE_PATH, run_name='__main__')
        captured = capsys.readouterr()
        assert "後者" in captured.out

    def test_normal_rni_equal(self, mocker, capsys):
        mocker.patch.object(sys, 'argv', ['database.py', '--rni'])
        mocker.patch('builtins.input', side_effect=['f1.csv', 'f2.csv'])
        mocker.patch('metrics.rni', return_value=(0.5, 0.5))
        runpy.run_path(_DATABASE_PATH, run_name='__main__')
        captured = capsys.readouterr()
        assert "同率" in captured.out

    def test_normal_val_option(self, mocker):
        mocker.patch.object(sys, 'argv', ['database.py', '--val'])
        mocker.patch('builtins.input', return_value='dummy_dir')
        mocker.patch('metrics.evaluation')
        runpy.run_path(_DATABASE_PATH, run_name='__main__')

    def test_normal_val_option_value_error(self, mocker, capsys):
        mocker.patch.object(sys, 'argv', ['database.py', '--val'])
        mocker.patch('builtins.input', return_value='bad_dir')
        mocker.patch('metrics.evaluation', side_effect=ValueError)
        runpy.run_path(_DATABASE_PATH, run_name='__main__')
        captured = capsys.readouterr()
        assert "誤り" in captured.out

    def test_normal_rniall_option(self, mocker):
        mock_df = mocker.Mock()
        mock_df.values = np.array([[0.0, 1.0], [1.0, 0.0]])
        mocker.patch.object(sys, 'argv', ['database.py', '--rniall'])
        inputs = ['f1.csv'] + ['f2.csv'] * 9
        mocker.patch('builtins.input', side_effect=inputs)
        mocker.patch('pandas.read_csv', return_value=mock_df)
        runpy.run_path(_DATABASE_PATH, run_name='__main__')

    def test_abnormal_no_args(self, mocker, capsys):
        mocker.patch.object(sys, 'argv', ['database.py'])
        runpy.run_path(_DATABASE_PATH, run_name='__main__')
        captured = capsys.readouterr()
        assert "オプション" in captured.out

    def test_abnormal_invalid_option(self, mocker, capsys):
        mocker.patch.object(sys, 'argv', ['database.py', '-unknown'])
        runpy.run_path(_DATABASE_PATH, run_name='__main__')
        captured = capsys.readouterr()
        assert "不正" in captured.out

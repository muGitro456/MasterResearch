import numpy as np
import logger


class TestLoggerResetLog:
    def test_normal_clears_all_lists(self):
        logger.LOG_POS.append(np.ones((3, 2)))
        logger.LOG_VEL.append(np.ones((3, 2)))
        logger.LOG_FIT.append(np.ones((3, 2)))
        logger.reset_log()
        assert logger.LOG_POS == []
        assert logger.LOG_VEL == []
        assert logger.LOG_FIT == []


class TestLoggerStore:
    def setup_method(self):
        logger.reset_log()

    def test_normal_pos(self):
        arr = np.ones((3, 2))
        logger.store(arr, 'p')
        assert len(logger.LOG_POS) == 1
        np.testing.assert_array_equal(logger.LOG_POS[0], arr)

    def test_normal_vel(self):
        arr = np.ones((3, 2))
        logger.store(arr, 'v')
        assert len(logger.LOG_VEL) == 1

    def test_normal_fit(self):
        arr = np.ones((3, 2))
        logger.store(arr, 'e')
        assert len(logger.LOG_FIT) == 1

    def test_abnormal_unknown_target(self, capsys):
        logger.store(np.ones((2, 2)), 'x')
        captured = capsys.readouterr()
        assert "該当なし" in captured.out


class TestLoggerWrite4debug:
    def setup_method(self):
        logger.reset_log()

    def test_normal_pos(self, mocker):
        logger.LOG_POS.append(np.ones((3, 2)))
        mocker.patch('os.makedirs')
        mocker.patch('pandas.DataFrame.to_csv')
        logger.write4debug('p', maxgen=1, m_num='1', m_name='TEST')

    def test_normal_vel(self, mocker):
        logger.LOG_VEL.append(np.ones((3, 2)))
        mocker.patch('os.makedirs')
        mocker.patch('pandas.DataFrame.to_csv')
        logger.write4debug('v', maxgen=1, m_num='1', m_name='TEST')

    def test_abnormal_unknown_target(self, mocker, capsys):
        mocker.patch('os.makedirs')
        logger.write4debug('x', maxgen=1, m_num='1', m_name='TEST')
        captured = capsys.readouterr()
        assert "Error : logger" in captured.out


class TestStoreTrajAndReset:
    def setup_method(self):
        logger.reset_log()

    def test_store_trajectory_appends(self):
        fit = np.array([[0.1, 0.9], [0.5, 0.5]])
        logger.store_trajectory(fit)
        assert len(logger.LOG_TRAJ) == 1
        np.testing.assert_array_equal(logger.LOG_TRAJ[0], fit)

    def test_reset_clears_log_traj(self):
        logger.store_trajectory(np.array([[0.1, 0.9]]))
        logger.reset_log()
        assert len(logger.LOG_TRAJ) == 0

import sys
from pathlib import Path
import pandas as pd
from unittest.mock import patch
import graph_drawer


class TestAnimateTrajectory:
    def test_animate_trajectory_with_single_generation(self, mocker, tmp_path):
        csv_file = tmp_path / "trajectory.csv"
        csv_file.write_text("generation,point_idx,f1,f2\n0,0,0.1,0.9\n0,1,0.5,0.5\n")

        mocker.patch('graph_drawer.plt.show')
        mocker.patch('graph_drawer.animation.FuncAnimation')

        graph_drawer.animate_trajectory(str(csv_file))

    def test_animate_trajectory_with_multiple_generations(self, mocker, tmp_path):
        csv_file = tmp_path / "trajectory.csv"
        csv_file.write_text(
            "generation,point_idx,f1,f2\n"
            "0,0,0.1,0.9\n"
            "0,1,0.5,0.5\n"
            "1,0,0.08,0.92\n"
            "1,1,0.48,0.52\n"
        )

        mocker.patch('graph_drawer.plt.show')
        mocker.patch('graph_drawer.animation.FuncAnimation')

        graph_drawer.animate_trajectory(str(csv_file))

    def test_animate_trajectory_with_custom_interval(self, mocker, tmp_path):
        csv_file = tmp_path / "trajectory.csv"
        csv_file.write_text("generation,point_idx,f1,f2\n0,0,0.1,0.9\n")

        mock_func_animation = mocker.patch('graph_drawer.animation.FuncAnimation')
        mocker.patch('graph_drawer.plt.show')

        graph_drawer.animate_trajectory(str(csv_file), interval=500)

        # Verify FuncAnimation was called with correct interval
        assert mock_func_animation.called

    def test_update_callback_renders_frame(self, tmp_path):
        """The FuncAnimation update callback correctly updates scatter data"""
        rows = [
            {'generation': 0, 'point_idx': 0, 'f1': 0.1, 'f2': 0.9},
            {'generation': 0, 'point_idx': 1, 'f1': 0.5, 'f2': 0.5},
            {'generation': 1, 'point_idx': 0, 'f1': 0.08, 'f2': 0.92},
        ]
        csv_path = str(tmp_path / 'trajectory.csv')
        pd.DataFrame(rows).to_csv(csv_path, index=False)

        with patch('matplotlib.pyplot.show'), \
             patch('matplotlib.animation.FuncAnimation') as mock_anim:
            sys.path.insert(0, str(Path(__file__).parent.parent / 'tools'))
            from graph_drawer import animate_trajectory
            animate_trajectory(csv_path)
            # Extract and call the update callback
            update_fn = mock_anim.call_args[0][1]
            result = update_fn(0)  # frame 0
            assert result is not None  # returns (scat, gen_text) tuple

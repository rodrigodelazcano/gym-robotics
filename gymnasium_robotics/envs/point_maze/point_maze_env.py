from os import path
from typing import Dict, List, Optional, Union

import numpy as np
from gymnasium import spaces

# from gymnasium_robotics.envs.point_maze.point_env import PointEnv
from gymnasium_robotics.envs.point_maze.maps import U_MAZE
from gymnasium_robotics.envs.point_maze.maze_env import MazeEnv
from gymnasium_robotics.envs.point_maze.point_env import PointEnv
from gymnasium_robotics.utils.mujoco_utils import MujocoModelNames


class PointMazeEnv(MazeEnv):
    """
    ### Description

    This environment was refactored from the [D4RL](https://github.com/Farama-Foundation/D4RL) repository, introduced by Justin Fu, Aviral Kumar, Ofir Nachum, George Tucker, and Sergey Levine
    in ["D4RL: Datasets for Deep Data-Driven Reinforcement Learning"](https://arxiv.org/abs/2004.07219).

    The task in the environment is for a 2-DoF ball that is force-actuated in the cartesian directions x and y, to reach a target goal in a closed maze. The variations of this environment
    can be initialized with different maze configurations and increasing levels of complexity. In the MuJoCo simulation the target goal can be visualized as a red static ball, while the actuated
    ball is green.

    The control frequency of the ball is of `f = 10 Hz`.

    ### Maze Variations

    The data structure to represent the mazes is a list of lists (`list[list]`) that contains the encoding of the discrete cell positions `(i,j)` of the maze. Each list inside the main list
    represents a row `i` of the maze, while the elements of the row are the intersections with the column index `j`.
    The cell encoding can have 5 different values:

    * `1: int` - Indicates that there is a wall in this cell.
    * `0: int` - Indicates that this cell is free for the agent and goal.
    * `"g": str` - Indicates that this cell can contain a goal. There can be multiple goals in the same maze and one of them will be randomly selected when the environment is reset.
    * `"r": str` - Indicates cells in which the agent can be initialized in when the environment is reset.
    * `"c": str` - Stands for combined cell and indicates that this cell can be initialized as a goal or agent reset location.

    The maze data structure is discrete. However the observations are continuous and variance is added to the goal and the agent's initial pose by adding a sammpled noise from a uniform distribution
    to the cell cartesian coordinate center in the MuJoCo simulation.

    There are three types of environment variations depending on the maze configuration:

    ```python
    # ID: PointMaze_UMaze-v3

    U_MAZE = [[1, 1, 1, 1, 1],
              [1, R, 0, 0, 1],
              [1, 1, 1, 0, 1],
              [1, G, 0, 0, 1],
              [1, 1, 1, 1, 1]]

    # ID: PointMaze_BigMaze-v3

    BIG_MAZE = [[1, 1, 1, 1, 1, 1, 1, 1],
                [1, R, 0, 1, 1, 0, 0, 1],
                [1, 0, 0, 1, 0, 0, 0, 1],
                [1, 1, 0, 0, 0, 1, 1, 1],
                [1, 0, 0, 1, 0, 0, 0, 1],
                [1, 0, 1, 0, 0, 1, 0, 1],
                [1, 0, 0, 0, 1, G, 0, 1],
                [1, 1, 1, 1, 1, 1, 1, 1]]

    # ID: PointMaze_HardestMaze-v3

    HARDEST_MAZE = [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                    [1, R, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1],
                    [1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1],
                    [1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
                    [1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1],
                    [1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 1],
                    [1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1],
                    [1, 0, 0, 1, 0, 0, 0, 1, 0, G, 0, 1],
                    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]
    ```

    Environment variations can also be found with multi-goal configurations, also referred to as `diverse`. Their `id` is the same as their
    default but adding the `_DG` string (`diverse goal`) to it:

    ```python
    # ID: PointMaze_BigMaze_DG-v3

    BIG_MAZE_DIVERSE_G = [[1, 1, 1, 1, 1, 1, 1, 1],
                          [1, R, 0, 1, 1, 0, 0, 1],
                          [1, 0, 0, 1, 0, 0, G, 1],
                          [1, 1, 0, 0, 0, 1, 1, 1],
                          [1, 0, 0, 1, 0, 0, 0, 1],
                          [1, G, 1, 0, 0, 1, 0, 1],
                          [1, 0, 0, 0, 1, G, 0, 1],
                          [1, 1, 1, 1, 1, 1, 1, 1]]

    # ID: PointMaze_HardestMaze_DG-v3

    HARDEST_MAZE_DIVERSE_G = [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                              [1, R, 0, 0, 0, 1, G, 0, 0, 0, 0, 1],
                              [1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1],
                              [1, 0, 0, 0, 0, G, 0, 1, 0, 0, G, 1],
                              [1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1],
                              [1, 0, G, 1, 0, 1, 0, 0, 0, 0, 0, 1],
                              [1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1],
                              [1, 0, 0, 1, G, 0, G, 1, 0, G, 0, 1],
                              [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]
    ```

    The last group of environment variations instantiates another type of `diverse` maze for which the goals and agent initialization locations are randomly selected at reset. The `id` of this environments is the same as their
    default but adding the `_DGR` string (`diverse goal/reset`) to it:

    ```python
    # ID: PointMaze_BigMaze_DGR-v3

    BIG_MAZE_DIVERSE_GR = [[1, 1, 1, 1, 1, 1, 1, 1],
                           [1, C, 0, 1, 1, 0, 0, 1],
                           [1, 0, 0, 1, 0, 0, C, 1],
                           [1, 1, 0, 0, 0, 1, 1, 1],
                           [1, 0, 0, 1, 0, 0, 0, 1],
                           [1, C, 1, 0, 0, 1, 0, 1],
                           [1, 0, 0, 0, 1, C, 0, 1],
                           [1, 1, 1, 1, 1, 1, 1, 1]]

    # ID: PointMaze_HardestMaze_DGR-v3

    HARDEST_MAZE_DIVERSE_GR = [[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
                               [1, C, 0, 0, 0, 1, C, 0, 0, 0, 0, 1],
                               [1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 0, 1],
                               [1, 0, 0, 0, 0, C, 0, 1, 0, 0, C, 1],
                               [1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1],
                               [1, 0, C, 1, 0, 1, 0, 0, 0, 0, 0, 1],
                               [1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1],
                               [1, 0, 0, 1, C, 0, C, 1, 0, C, 0, 1],
                               [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]
    ```

    Finally, any `Point Maze` environment can be initialized with a custom maze map by setting the `maze_map` argument like follows:

    ```python
    import gymnasium as gym

    map = [[1, 1, 1, 1, 1],
           [1, C, 0, C, 1],
           [1, 1, 1, 1, 1]]

    env = gym.make('PointMaze_UMaze-v3', maze_map=map)
    ```

    ### Action Space

    The action space is a `Box(-1.0, 1.0, (2,), float32)`. An action represents the linear force exerted on the green ball in the x and y directions.
    In addition, the ball velocity is clipped in a range of `[-5, 5] m/s` in order for it not to grow unbounded.

    | Num | Action                          | Control Min | Control Max | Name (in corresponding XML file)| Joint | Unit     |
    | --- | --------------------------------| ----------- | ----------- | --------------------------------| ----- | ---------|
    | 0   | Linear force in the x direction | -1          | 1           | motor_x                         | slide | force (N)|
    | 1   | Linear force in the x direction | -1          | 1           | motor_y                         | slide | force (N)|

    ### Observation Space

    The observation is a `goal-aware observation space`. It consists of a dictionary with information about the robot's position and goal. The dictionary consists of the following 3 keys:
    `observation`: its value is an `ndarray` of shape `(4,)`. It consists of kinematic information of the force-actuated ball. The elements of the array correspond to the following:

        | Num | Observation                                              | Min    | Max    | Joint Name (in corresponding XML file) |Joint Type| Unit          |
        |-----|--------------------------------------------------------- |--------|--------|----------------------------------------|----------|---------------|
        | 0   | x coordinate of the green ball in the MuJoCo simulation  | -Inf   | Inf    | ball_x                                 | slide    | position (m)  |
        | 1   | y coordinate of the green ball in the MuJoCo simulation  | -Inf   | Inf    | ball_y                                 | slide    | position (m)  |
        | 2   | Green ball linear velocity in the x direction            | -Inf   | Inf    | ball_x                                 | slide    | velocity (m/s)|
        | 3   | Green ball linear velocity in the y direction            | -Inf   | Inf    | ball_y                                 | slide    | velocity (m/s)|

    desired_goal`: this key represents the final goal to be achieved. In this environment it is a 2-dimensional `ndarray`, `(2,)`, that consists of the two cartesian coordinates of the desired final block position `[x,y]`. The elements of the array are the following:

        | Num | Observation                                  | Min    | Max    | Site Name (in corresponding XML file) |Unit          |
        |-----|----------------------------------------------|--------|--------|---------------------------------------|--------------|
        | 0   | Final goal ball position in the x coordinate | -Inf   | Inf    | target0                               | position (m) |
        | 1   | Final goal ball position in the y coordinate | -Inf   | Inf    | target0                               | position (m) |

    `achieved_goal`: this key represents the current state of the green ball, as if it would have achieved a goal. This is useful for goal orientated learning algorithms such as those that use [Hindsight Experience Replay](https://arxiv.org/abs/1707.01495) (HER).
     The value is an `ndarray` with shape `(2,)`. The elements of the array are the following:

        | Num | Observation                                    | Min    | Max    | Site Name (in corresponding XML file) |Unit          |
        |-----|------------------------------------------------|--------|--------|---------------------------------------|--------------|
        | 0   | Current goal ball position in the x coordinate | -Inf   | Inf    | object0                               | position (m) |
        | 1   | Current goal ball position in the y coordinate | -Inf   | Inf    | object0                               | position (m) |

    ### Rewards

    The reward can be initialized as `sparse` or `dense`:
    - *sparse*: the returned reward can have two values: `0` if the ball hasn't reached its final target position, and `1` if the ball is in the final target position (the ball is considered to have reached the goal if the Euclidean distance between both is lower than 0.5 m).
    - *dense*: the returned reward is the negative Euclidean distance between the achieved goal position and the desired goal.

    To initialize this environment with one of the mentioned reward functions the type of reward must be specified in the id string when the environment is initialized. For `sparse` reward the id is the default of the environment, `PointMaze_UMaze-v3`. However, for `dense`
    reward the id must be modified to `FetchPickAndPlaceDense-v2` and initialized as follows:

    ```python
    import gymnasium as gym

    env = gym.make('PointMaze_UMazeDense-v3')
    ```

    ### Starting State

    The goal and initial placement of the ball in the maze follows the same structure for all environments. A discrete cell `(i,j)` is selected for the goal and agent's initial position as previously menitoned in the **Maze** section.
    Then this cell index is converted to its cell center as an `(x,y)` continuous Cartesian coordinates in the MuJoCo simulation. Finally, a sampled noise from a uniform distribution with range `[-0.25,0.25]m` is added to the
    cell's center x and y coordinates. This allows to create a richer goal distribution.

    The goal and initial position of the agent can also be specified by the user when the episode is reset. This is done by passing the dictionary argument `options` to the gymnasium reset() function. This dictionary expects one or both of
    the following keys:

    * `goal_cell`: `numpy.ndarray, shape=(2,0), type=int` - Specifies the desired `(i,j)` cell location of the goal. A uniform sampled noise will be added to the continuous coordinates of the center of the cell.
    * `reset_cell`: `numpy.ndarray, shape=(2,0), type=int` - Specifies the desired `(i,j)` cell location of the reset initial agent position. A uniform sampled noise will be added to the continuous coordinates of the center of the cell.

    ### Episode End

    *`truncated` - The episode will be `truncated` when the duration reaches a total of `max_episode_steps`.
    * `terminated` - The task can be set to be continuing with the `continuing_task` argument. In this case the episode will never terminate, instead the goal location is randomly selected again. If the task is set not to be continuing the
    episode will be terminated when the Euclidean distance to the goal is less or equal to 0.5.

    ### Arguments

    * `maze_map` - Optional argument to initialize the environment with a custom maze map.
    * `continuing_task` - If set to `True` the episode won't be terminated when reaching the goal, instead a new goal location will be generated. If `False` the environment is terminated when the ball reaches the final goal.

    Note that, the maximum number of timesteps before the episode is `truncated` can be increased or decreased by specifying the `max_episode_steps` argument at initialization. The default value is 50. For example,
    to increase the total number of timesteps to 100 make the environment as follows:

    ```python
    import gymnasium as gym

    env = gym.make('PointMaze_UMaze-v3', max_episode_steps=100)
    ```

    ### Version History
    * v3: refactor version of the D4RL environment, also create dependency on newest [mujoco python bindings](https://mujoco.readthedocs.io/en/latest/python.html) maintained by the MuJoCo team in Deepmind.
    * v2 & v1: legacy versions in the [D4RL](https://github.com/Farama-Foundation/D4RL).
    """

    metadata = {
        "render_modes": [
            "human",
            "rgb_array",
            "depth_array",
        ],
        "render_fps": 50,
    }

    def __init__(
        self,
        maze_map: List[List[Union[str, int]]] = U_MAZE,
        render_mode: Optional[str] = None,
        reward_type: str = "sparse",
        continuing_task: bool = True,
        **kwargs,
    ):
        point_xml_file_path = path.join(
            path.dirname(path.realpath(__file__)), "../assets/point/point.xml"
        )
        super().__init__(
            agent_xml_path=point_xml_file_path,
            maze_map=maze_map,
            maze_size_scaling=1,
            maze_height=0.4,
            reward_type=reward_type,
            continuing_task=continuing_task,
            **kwargs,
        )

        self.point_env = PointEnv(
            xml_file=self.tmp_xml_file_path, render_mode=render_mode, **kwargs
        )
        self._model_names = MujocoModelNames(self.point_env.model)
        self.target_site_id = self._model_names.site_name2id["target"]

        self.action_space = self.point_env.action_space
        obs_shape: tuple = self.point_env.observation_space.shape
        self.observation_space = spaces.Dict(
            dict(
                observation=spaces.Box(
                    -np.inf, np.inf, shape=obs_shape, dtype="float64"
                ),
                achieved_goal=spaces.Box(-np.inf, np.inf, shape=(2,), dtype="float64"),
                desired_goal=spaces.Box(-np.inf, np.inf, shape=(2,), dtype="float64"),
            )
        )

        self.render_mode = render_mode

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        **kwargs,
    ):
        super().reset(seed=seed, **kwargs)
        self.point_env.init_qpos[:2] = self.reset_pos

        obs, info = self.point_env.reset(seed=seed)
        obs_dict = self._get_obs(obs)

        return obs_dict, info

    def step(self, action):
        obs, _, _, _, info = self.point_env.step(action)
        obs_dict = self._get_obs(obs)

        terminated = self.compute_terminated(obs_dict["achieved_goal"], self.goal, info)
        truncated = self.compute_truncated(obs_dict["achieved_goal"], self.goal, info)

        reward = self.compute_reward(obs_dict["achieved_goal"], self.goal, info)

        return obs_dict, reward, terminated, truncated, info

    def update_target_site_pos(self):
        self.point_env.model.site_pos[self.target_site_id] = np.append(
            self.goal, self.maze.maze_height / 2 * self.maze.maze_size_scaling
        )

    def _get_obs(self, point_obs) -> Dict[str, np.ndarray]:
        achieved_goal = point_obs[2:]
        return {
            "observation": point_obs.copy(),
            "achieved_goal": achieved_goal.copy(),
            "desired_goal": self.goal.copy(),
        }

    def render(self):
        self.point_env.render()

    def close(self):
        super().close()
        self.point_env.close()
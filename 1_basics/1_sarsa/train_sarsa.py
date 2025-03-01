import gymnasium as gym
import numpy as np
import random
import time
from tqdm import tqdm

# from sarsa import SARSA
from sarsa_solution import SARSA


CONFIG = {
    "total_steps": 1000000,
    "episode_length": 100,
    "eval_episodes": 100,
    "eval_freq": 100000,
    "gamma": 0.99,
    "alpha": 1e-1,
    "epsilon": 0.9,
}

RENDER = False


def evaluate(env, agent, max_steps, eval_episodes):
    """
    Evaluate configuration on given environment when initialised with given Q-table

    :param env (gym.Env): environment to execute evaluation on
    :param agent (Agent): agent to act in environment
    :param max_steps (int): max number of steps per evaluation episode
    :param eval_episodes (int): number of evaluation episodes
    :return (float, float): mean and std of returns received over episodes
    """
    episodic_returns = []
    for eps_num in range(eval_episodes):
        obs, _ = env.reset()
        episodic_return = 0
        done = False
        steps = 0

        while not done and steps < max_steps:
            act = agent.act(obs)
            n_obs, reward, terminated, truncated, info = env.step(act)
            done = terminated or truncated

            episodic_return += reward
            steps += 1

            obs = n_obs

        episodic_returns.append(episodic_return)

    mean_return = np.mean(episodic_returns)
    std_return = np.std(episodic_returns)

    return mean_return, std_return


def train(env, eval_env, config):
    """
    Train and evaluate SARSA on given environment with provided hyperparameters

    :param env (gym.Env): environment to execute evaluation on
    :param config (Dict[str, float]): configuration dictionary containing hyperparameters
    :return (List[float], Dict[(Obs, Act)]):
        list of means of evaluation returns, final Q-table
    """
    agent = SARSA(
            num_actions=env.action_space.n,
            gamma=config["gamma"],
            epsilon=config["epsilon"],
            alpha=config["alpha"],
    )

    completed_steps = 0
    completed_evaluations = 0
    evaluation_return_means = []

    with tqdm(total=config["total_steps"]) as pbar:
        while completed_steps < config["total_steps"]:
            obs, _ = env.reset()
            episodic_return = 0
            steps = 0
            done = False

            # take first action
            act = agent.act(obs)

            while not done and steps < config["episode_length"]:
                n_obs, reward, terminated, truncated, info = env.step(act)
                done = terminated or truncated
                steps += 1
                episodic_return += reward

                agent.schedule_hyperparameters(completed_steps, config["total_steps"])
                n_act = agent.act(n_obs)
                agent.learn(obs, act, reward, n_obs, n_act, done)

                obs = n_obs
                act = n_act

            pbar.update(steps)
            completed_steps += steps

            if completed_evaluations < completed_steps / config["eval_freq"]:
                mean_return, std_return = evaluate(
                        eval_env,
                        agent,
                        config["episode_length"],
                        config["eval_episodes"],
                )
                completed_evaluations += 1
                pbar.write(f"EVALUATION: {completed_steps} STEPS - RETURNS {mean_return} +/- {std_return}")
                evaluation_return_means.append(mean_return)

    return evaluation_return_means, agent.q_table


if __name__ == "__main__":
    env = gym.make("Taxi-v3")
    eval_env = gym.make("Taxi-v3", render_mode="human") if RENDER else env
    returns, q_table = train(env, eval_env, CONFIG)
    if RENDER:
        eval_env.close()
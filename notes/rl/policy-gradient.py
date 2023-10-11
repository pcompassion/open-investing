import gym
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import sys
print(sys.path)
class PolicyNet(nn.Module):
    def __init__(self, n_states, n_actions):
        super(PolicyNet, self).__init__()
        self.fc = nn.Linear(n_states, n_actions)
        
    def forward(self, x):
        return torch.softmax(self.fc(x), dim=-1)

def sample_action(policy, state):
    state_one_hot = torch.eye(n_states)[state]
    action_probs = policy(state_one_hot)
    return torch.multinomial(action_probs, 1).item()

env = gym.make('FrozenLake-v0', is_slippery=False)
n_states = env.observation_space.n
n_actions = env.action_space.n

policy = PolicyNet(n_states, n_actions)
optimizer = optim.Adam(policy.parameters(), lr=0.01)

for episode in range(500):
    episode_rewards = []
    episode_log_probs = []
    state = env.reset()
    done = False

    while not done:
        state_one_hot = torch.eye(n_states)[state]
        action_probs = policy(state_one_hot)
        action = torch.multinomial(action_probs, 1).item()
        log_prob = torch.log(action_probs[action])

        next_state, reward, done, _ = env.step(action)

        episode_rewards.append(reward)
        episode_log_probs.append(log_prob)

        state = next_state

    total_episode_reward = sum(episode_rewards)

    loss = []
    for log_prob in episode_log_probs:
        loss.append(-log_prob * total_episode_reward)
    loss = torch.stack(loss).sum()

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

def test_policy(policy, num_episodes=100):
    total_rewards = 0.0
    for episode in range(num_episodes):
        state = env.reset()
        episode_rewards = 0.0
        done = False
        while not done:
            state_one_hot = torch.eye(n_states)[state]
            action_probs = policy(state_one_hot)
            action = torch.argmax(action_probs).item()
            state, reward, done, _ = env.step(action)
            episode_rewards += reward
        total_rewards += episode_rewards
    return total_rewards / num_episodes

print("Policy success rate:", test_policy(policy) * 100, "%")

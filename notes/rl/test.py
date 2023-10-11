import numpy as np

# Define the environment
n_states = 16  # For the 4x4 grid
n_actions = 4  # Up, Down, Left, Right

# Initialize the Q-table with zeros
Q = np.zeros((n_states, n_actions))


frozen_lake_list = [
    'SFFF',
    'FHFH',
    'FFFH',
    'HFFG'
]

frozen_lake = np.array([list(row) for row in frozen_lake_list])

def state_to_coord(state):
    """Convert a state number to a coordinate (i, j) on the grid."""
    return divmod(state, 4)

def coord_to_state(coord):
    """Convert a grid coordinate (i, j) to a state number."""
    i, j = coord
    return i * 4 + j

def next_state(state, action):
    """Determine the next state given an action."""
    i, j = state_to_coord(state)
    if action == 0:  # UP
        i = max(i - 1, 0)
    elif action == 1:  # DOWN
        i = min(i + 1, 3)
    elif action == 2:  # LEFT
        j = max(j - 1, 0)
    elif action == 3:  # RIGHT
        j = min(j + 1, 3)
    return coord_to_state((i, j))
    
def get_reward(state):
    i, j = state_to_coord(state)
    cell = frozen_lake[i][j]
    if cell == 'G':
        return 1
    elif cell == 'H':
        return 0
    else:
        return -0.01
   
def choose_action(state, epsilon):
    if np.random.uniform(0, 1) < epsilon:
        return np.random.choice(n_actions)  # Explore: choose a random action
    else:
        return np.argmax(Q[state, :])  # Exploit: choose the action with max Q-value


# Hyperparameters
alpha = 0.8  # learning rate
gamma = 0.95  # discount factor
epsilon = 0.1  # exploration rate
total_episodes = 10000  # number of episodes to train on

# Q-learning Loop
for episode in range(total_episodes):
    state = 0  # start at the beginning of the lake
    while frozen_lake[state_to_coord(state)] != 'G' and frozen_lake[state_to_coord(state)] != 'H':  # not at goal or hole
        # Choose action using epsilon-greedy strategy
        action = choose_action(state, epsilon)

        # Take action and observe new state and reward
        new_state = next_state(state, action)
        reward = get_reward(new_state)

        # Update Q-value using the Q-learning update rule
        Q[state, action] = (1 - alpha) * Q[state, action] + \
                           alpha * (reward + gamma * np.max(Q[new_state, :]))

        # Move to the next state
        state = new_state

    # Optionally reduce epsilon over episodes to reduce exploration as we learn
    # epsilon = epsilon * 0.995  # for example

print("Training complete!")


policy = np.argmax(Q, axis=1)

def test_policy(policy, num_episodes):
    success_count = 0

    for episode in range(num_episodes):
        state = 0  # start at the beginning of the lake
        while frozen_lake[state_to_coord(state)] != 'G' and frozen_lake[state_to_coord(state)] != 'H':
            action = policy[state]  # choose action from policy
            print(f"action: {action}")
            state = next_state(state, action)

        if frozen_lake[state_to_coord(state)] == 'G':
            success_count += 1  # Increment success count if goal reached

    success_rate = success_count / num_episodes
    return success_rate

num_episodes = 1000

success_rate = test_policy(policy, num_episodes)

print(f"Policy success rate over {num_episodes} episodes: {success_rate * 100:.2f}%")

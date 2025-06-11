import numpy as np
import random
from collections import deque
from constants import *
from tensorflow.keras import models,layers,optimizers
from env import Env

state_size = ROWS * COLS * MAX_SLICES_PER_PLATE + MAX_SLICES_PER_PLATE - 1
action_size = ROWS * COLS
gamma = 0.95
epsilon = 1.0
epsilon_min = 0.1
epsilon_decay = 0.995
batch_size = 64
episodes = 2000
memory = deque(maxlen=20000)

model = models.Sequential([
    layers.Input(shape=(state_size,)),
    layers.Dense(256,activation="relu"),
    layers.Dense(action_size,activation="linear")
])
model.compile(loss="mse",optimizer=optimizers.Adam(learning_rate=0.001))

env = Env()

def act(state,epsilon):
    if np.random.rand() <= epsilon:
        return random.randrange(action_size)

    q_values = model.predict(state[np.newaxis],verbose=0)[0]
    return np.argmax(q_values)

file = open("training.txt","a")

for episode in range(episodes):
    state = env.reset()
    total_reward = 0

    for step_num in range(200):
        action = act(state, epsilon)
        next_state, reward, done = env.step(action)
        total_reward += reward

        memory.append((state, action, reward, next_state, done))
        state = next_state

        if done:
            break

        if len(memory) >= batch_size:
            minibatch = random.sample(memory, batch_size)
            states = np.array([x[0] for x in minibatch])
            targets = model.predict(states, verbose=0)
            next_states = np.array([x[3] for x in minibatch])
            targets_next = model.predict(next_states, verbose=0)

            for i, (s, a, r, s_next, d) in enumerate(minibatch):
                targets[i][a] = r if d else r + gamma * np.max(targets_next[i])

            model.fit(states, targets, epochs=1, verbose=0)

    epsilon = max(epsilon_min,epsilon*epsilon_decay)
    print(f"Episode {episode+1}, Total reward: {total_reward}, Epsilon: {epsilon:.3f}")
    file.write(f"Episode {episode+1}, Total reward: {total_reward}, Epsilon: {epsilon:.3f}\n")

file.close()
print(f"Used memory: {len(memory)}")
model.save("cake_sort_model.h5")

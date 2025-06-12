import numpy as np
import random
from collections import deque
from statistics import *
from constants import *
from tensorflow.keras.models import Model
from tensorflow.keras import layers,optimizers,Input
from env import Env

state_size = ROWS * COLS * MAX_SLICES_PER_PLATE + MAX_SLICES_PER_PLATE - 1
action_size = ROWS * COLS
gamma = 0.95
epsilon = 1.0
epsilon_min = 0.1
epsilon_decay = 0.98
batch_size = 64
episodes = 1000
memory = deque(maxlen=20000)

full_input = Input(shape=(125,))
board_input = layers.Lambda(lambda x: x[:,:120])(full_input)
plate_input = layers.Lambda(lambda x: x[:,120:])(full_input)
conv_reshaped = layers.Reshape((5,4,6))(board_input)
board_out = layers.Conv2D(32,(3,3),activation="relu",padding="same")(conv_reshaped)
board_out = layers.Flatten()(board_out)
concat = layers.Concatenate()([board_out,plate_input])
output = layers.Dense(action_size,activation="linear")(concat)
model = Model(inputs=full_input,outputs=output)
model.compile(loss="mse",optimizer=optimizers.Adam(learning_rate=10e-5))

env = Env()

def stats(array):
    print(
        "Statistics:",
        f"{len(array)=}",f"{max(array)=}",f"{mean(array)=}",f"{median(array)=}",
        sep="\n"
    )

def act(state, epsilon):
    q_values = model.predict(state[np.newaxis], verbose=0)[0]

    valid_actions = []
    for action in range(action_size):
        row, col = divmod(action, COLS)
        if not env.game.board.get_plate_number(row, col):
            valid_actions.append(action)

    if not valid_actions:
        return random.randrange(action_size)

    if np.random.rand() <= epsilon:
        return random.choice(valid_actions)

    masked_q = np.full_like(q_values, -np.inf)
    for a in valid_actions:
        masked_q[a] = q_values[a]

    return np.argmax(masked_q)

file = open("training.txt","a")
rewards = []

for episode in range(episodes):
    state = env.reset()
    total_reward = 0
    total_score = 0
    losses = []

    for step_num in range(200):
        action = act(state, epsilon)
        next_state,score,bonus,done = env.step(action)
        total_score+=score
        total_reward+=score+bonus

        memory.append((state, action, score+bonus, next_state, done))
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

            history = model.fit(states, targets, epochs=1, verbose=0)
            losses.append(history.history["loss"][0])
    else:
        print("HEI")
        quit()

    epsilon = max(epsilon_min,epsilon*epsilon_decay)
    rewards.append(total_score)
    print(f"Episode {episode+1}, Total reward: {total_reward}, Mean loss: {mean(losses) if losses else float('-inf')}, Epsilon: {epsilon:.3f}")
    stats(rewards)
    file.write(f"Episode {episode+1}, Total reward: {total_reward}, Mean loss: {mean(losses) if losses else float('-inf')}, Epsilon: {epsilon:.3f}\n")

file.close()
print(f"Used memory: {len(memory)}")
model.save("cake_sort_model.h5")

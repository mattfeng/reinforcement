from experiment import Experiment
from agent import VanillaPolicyGradientAgent
from observers import StepObserver
from skimage import color
from skimage.transform import resize
from sklearn.preprocessing import binarize
from collections import deque
import time
import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import numpy as np

class PongExperiment(Experiment):
    def _define_agent(self):
        self.agent = VanillaPolicyGradientAgent(self.env,
            self.sess, self.hparams, input_shape=(6400,))
        self.agent.add_observer(StepObserver(self.agent))

    def _accumulate(self, r):
        r = np.array(r)
        discounted_r = np.zeros_like(r)
        running_add = 0
        for t in reversed(range(0, r.size)):
            # reset the sum, since this was a game boundary (pong specific!)
            if r[t] != 0:
                running_add = 0
            running_add = running_add * self.gamma + r[t]
            discounted_r[t] = running_add
        
        discounted_r -= np.mean(discounted_r)
        discounted_r /= np.std(discounted_r)

        return discounted_r

    def _preprocess(self, I):
        I = I[35:195] # crop
        I = I[::2,::2,0] # downsample by factor of 2
        I[I == 144] = 0 # erase background (background type 1)
        I[I == 109] = 0 # erase background (background type 2)
        I[I != 0] = 1 # everything else (paddles, ball) just set to 1
        return I.astype(np.float32)

    def _process(self, s, s_):
        s = self._preprocess(s)
        s_ = self._preprocess(s_)

        # compute the difference, flatten
        diff = s - s_
        diff = np.ravel(diff)

        return diff

    def rollout(self):
        s = self.env.reset()
        s_, _, _, _ = self.env.step(0)

        states, actions, rewards = [], [], []
        done = False

        while not done:
            if self.render:
                self.env.render()
            
            if self.test_mode:
                time.sleep(0.02)
            
            ps = self._process(s, s_)
            a = self.agent.act(ps)

            s = s_
            s_, r, done, _ = self.env.step(a)
            if r == 1:
                print("+1!!")
            elif r == -1:
                print("-1")

            states.append(ps)
            actions.append(a)
            rewards.append(r)
            
        advantages = self._accumulate(rewards)
        return states, actions, rewards, advantages

if __name__ == "__main__":
    import gym
    import matplotlib.pyplot as plt

    env = gym.make("PongDeterministic-v0")
    s = env.reset()
    s[s[:, :] == [109, 118, 43]] = 0
    s[~(s[:, :] == [0, 0, 0])] = 255
    s = s[32:192, :, 0]
    s = resize(s, (84, 84), anti_aliasing=False)
    s /= 255
    s -= 0.5
    
    # s = resize(s, (84, 84), anti_aliasing=False)
    plt.imshow(s)
    plt.show()

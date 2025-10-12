# /ai/deep_q_network.py
import torch
import torch.nn as nn
import torch.optim as optim


class QNetwork(nn.Module):
    """Simple fully connected Q-network."""

    def __init__(self, state_dim, action_dim, hidden=128):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(state_dim, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden),
            nn.ReLU(),
            nn.Linear(hidden, action_dim),
        )

    def forward(self, x):
        return self.net(x)


class DQNLearner:
    """Manages neural Q-learning updates."""

    def __init__(self, state_dim, action_dim, lr=1e-3, gamma=0.95, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.q_net = QNetwork(state_dim, action_dim).to(self.device)
        self.target_net = QNetwork(state_dim, action_dim).to(self.device)
        self.target_net.load_state_dict(self.q_net.state_dict())
        self.optimizer = optim.Adam(self.q_net.parameters(), lr=lr)
        self.gamma = gamma
        self.loss_fn = nn.MSELoss()
        self.update_counter = 0

    def update(self, batch):
        """Perform one DQN update step."""
        states, actions, rewards, next_states = batch
        states = torch.tensor(states, dtype=torch.float32).to(self.device)
        actions = torch.tensor(actions, dtype=torch.long).to(self.device)
        rewards = torch.tensor(rewards, dtype=torch.float32).to(self.device)
        next_states = torch.tensor(next_states, dtype=torch.float32).to(self.device)

        q_values = self.q_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)
        next_q = self.target_net(next_states).max(1)[0].detach()
        targets = rewards + self.gamma * next_q

        loss = self.loss_fn(q_values, targets)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        self.update_counter += 1
        if self.update_counter % 20 == 0:
            self.target_net.load_state_dict(self.q_net.state_dict())

        return loss.item()

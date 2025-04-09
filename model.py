import torch
import torch.nn as nn



def attn_forward(x, attention, row_weights, col_weights):
    weighted = x * attention  # (1, H, W)
    row_sum = weighted.mean(dim=2)  # (1, H)
    col_sum = weighted.mean(dim=1)  # (1, W)
    row_output = (row_sum * row_weights).mean(dim=1)  # (1,)
    col_output = (col_sum * col_weights).mean(dim=1)  # (1,)
    output = torch.stack([col_output, row_output], dim=1)  # (1, 2)
    return torch.sigmoid(output)


class EfficientEyeTracker(nn.Module):
    def __init__(self, h, w, lr=0.2):
        """
        Initialize the EfficientEyeTracker model and its training components.

        Args:
            h (int): Height of the input image
            w (int): Width of the input image
            lr (float): Learning rate for the optimizer
        """
        super().__init__()

        self.attention = nn.Parameter(torch.ones(h, w))
        self.row_weights = nn.Parameter(torch.ones(h))
        self.col_weights = nn.Parameter(torch.ones(w))

        self.optimizer = torch.optim.RMSprop(self.parameters(), lr=lr)
        self.loss_fn = nn.MSELoss()

    def forward(self, x):
        return attn_forward(x, self.attention, self.row_weights, self.col_weights)
    
    def predict(self, x):
        self.eval()
        with torch.no_grad():
            return self.forward(x)

    def update(self, x, target):
        """
        Perform one training step.

        Args:
            x (Tensor): Input tensor of shape (1, H, W)
            target (Tensor): Target tensor of shape (1, 2)

        Returns:
            float: Loss value, Tensor: prediction
        """
        self.train()
        self.optimizer.zero_grad()
        pred = self.forward(x)
        loss = self.loss_fn(pred, target)
        loss.backward()
        self.optimizer.step()
        return loss.item(), pred


class AvgOptimizationTracker:
    def __init__(self, h: int, w: int, k: int):
        """
        This model works by randomizing the weights at each train prediction.
        The randomized weights are then weighted by their performance and tracked using a running
        average to determine the best weights.
        """

        self.k = k
        self.h = h
        self.w = w
        self.num_steps = 0
        self._avg_attention_sum = torch.ones(h, w)
        self._avg_row_weights_sum = torch.ones(h)
        self._avg_col_weights_sum = torch.ones(w)

    @property
    def avg_attention(self):
        return self._avg_attention_sum / self.num_steps
    
    @property
    def avg_row_weights(self):
        return self._avg_row_weights_sum / self.num_steps
    
    @property
    def avg_col_weights(self):
        return self._avg_col_weights_sum / self.num_steps
    
    def train_forward(self, x):
        """
        Perform one training step.

        Args:
            x (Tensor): Input tensor of shape (1, H, W)
            target (Tensor): Target tensor of shape (1, 2)

        Returns:
            float: Loss value, Tensor: prediction
        """

        self.num_steps += 1

        # random uniform weights k, h, w for atn
        attention = torch.rand(self.k, self.h, self.w)
        row_weights = torch.rand(self.k, self.h)
        col_weights = torch.rand(self.k, self.w)

        preds = attn_forward(x, attention, row_weights, col_weights)
        return preds


if __name__ == "__main__":
    model = AvgOptimizationTracker(h=64, w=64, k=16)
    x = torch.rand(64, 64)
    pred = model.train_forward(x)
    print(pred.shape)
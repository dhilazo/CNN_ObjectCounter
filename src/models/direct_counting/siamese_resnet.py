import torch
import torch.nn.functional as F
import torchvision
from torch import Tensor, nn


class FullyConnectedLayers(nn.Module):
    def __init__(self):
        super(FullyConnectedLayers, self).__init__()
        self.fc1 = nn.Linear(2048, 1024)
        self.fc2 = nn.Linear(1024, 512)
        self.fc3 = nn.Linear(512, 128)

        self.dropout = nn.Dropout(0.2)

    def forward(self, x: Tensor) -> Tensor:
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = F.relu(self.fc2(x))
        x = self.dropout(x)
        x = F.relu(self.fc3(x))
        x = self.dropout(x)

        return x


class SiameseResNet(nn.Module):
    def __init__(self, output_size: int = 10):
        super(SiameseResNet, self).__init__()
        self.resnet_model = torchvision.models.resnet50(pretrained=True)
        self.resnet_model.fc = FullyConnectedLayers()
        self.output = nn.Linear(128, output_size)

    def forward(self, x: Tensor, x_object: Tensor) -> Tensor:
        x = self.resnet_model(x)

        x_object = self.resnet_model(x_object)

        x_joined = torch.abs(x - x_object)
        x_joined = self.output(x_joined)
        return x_joined

from typing import Tuple

import torch.nn as nn
import torch.utils.data
from torch import Tensor

from models.custom_conv_transpose2d import CustomConvTranspose2d


class CNNEncoder(nn.Module):
    """
    Convolutional Encoder module.

    Args:
        - bottleneck_size (int): output size of the last linear layer.
        - channels (int, optional): number of channels of the decoded image.
    """

    def __init__(self, bottleneck_size: int, channels: int = 3):
        super(CNNEncoder, self).__init__()

        self.bottle_neck_size = bottleneck_size

        self.encoder = nn.Sequential(
            # input is channels x 63 x 63
            nn.Conv2d(channels, 32, 7, stride=2, padding=1),
            nn.ReLU(),
            # nn.MaxPool2d(2, 2),
            # state size. 32 x 30 x 30
            nn.Conv2d(32, 64, 5, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            # nn.MaxPool2d(2, 2),
            # state size. 64 x 14 x 14
            nn.Conv2d(64, 128, 5, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            # nn.MaxPool2d(2, 2),
            # state size. 128 x 6 x 6
            nn.Conv2d(128, 256, 3, stride=2, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            # nn.MaxPool2d(2, 2),
            # state size. 256 x 3 x 3
            nn.Conv2d(256, 512, 3, stride=2),
            nn.BatchNorm2d(512),
            nn.ReLU(),
            # nn.MaxPool2d(2, 2),
            # state size. 512 x 1 x 1
            nn.Conv2d(512, 1024, 1),
            nn.BatchNorm2d(1024),
            nn.ReLU(),
            # nn.Sigmoid()
        )

        self.fc11 = nn.Linear(1024, self.bottle_neck_size)
        self.fc12 = nn.Linear(1024, self.bottle_neck_size)

        self.relu = nn.ReLU()

    def forward(self, x: Tensor) -> Tuple[Tensor, Tensor]:
        x = self.encoder(x)
        return self.fc11(x.view(-1, 1024)), self.fc12(x.view(-1, 1024))


class CNNDecoder(nn.Module):
    """
    Convolutional Decoder module.

    Args:
        - bottleneck_size (int): input size of the first linear layer.
        - channels (int, optional): number of channels of the decoded image.
    """

    def __init__(self, bottleneck_size: int, channels: int = 3):
        super(CNNDecoder, self).__init__()

        self.bottle_neck_size = bottleneck_size

        self.fc4 = nn.Linear(self.bottle_neck_size, 1024)

        self.decoder = nn.Sequential(
            CustomConvTranspose2d(1024, 512, 1, output_size=(1, 1)),
            nn.BatchNorm2d(512),
            nn.ReLU(),
            # state size. 512 x 6 x 5
            # nn.MaxUnpool2d(2, 2),
            CustomConvTranspose2d(512, 256, 3, stride=2, output_size=(3, 3)),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            # state size. 256 x 13 x 11
            # nn.MaxUnpool2d(2, 2),
            CustomConvTranspose2d(256, 128, 3, stride=2, padding=1, output_size=(6, 6)),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            # state size. 128 x 26 x 21
            # nn.MaxUnpool2d(2, 2),
            CustomConvTranspose2d(128, 64, 5, stride=2, padding=1, output_size=(14, 14)),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            # state size. 64 x 53 x 43
            # nn.MaxUnpool2d(2, 2),
            CustomConvTranspose2d(64, 32, 5, stride=2, padding=1, output_size=(30, 30)),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            # state size. 32 x 107 x 87
            # nn.MaxUnpool2d(2, 2),
            CustomConvTranspose2d(32, channels, 7, stride=2, padding=1, output_size=(63, 63)),
        )

        self.relu = nn.ReLU()
        self.fc3_bn = nn.BatchNorm1d(512)
        self.fc4_bn = nn.BatchNorm1d(1024)

    def forward(self, x: Tensor) -> Tensor:
        x = self.fc4_bn(self.fc4(x))
        x = x.view(-1, 1024, 1, 1)
        x = self.decoder(x)
        x = torch.tanh(x)
        return x


class ConvVAEGMN(nn.Module):
    def __init__(self, channels: int = 3):
        super(ConvVAEGMN, self).__init__()

        # Encoder
        self.encoder = CNNEncoder(512, channels=channels)

        # Decoder
        self.decoder = CNNDecoder(512, channels=channels)

    @staticmethod
    def reparametrize(mu: Tensor, logvar: Tensor) -> Tensor:
        std = logvar.mul(0.5).exp_()

        eps = torch.FloatTensor(std.size()).normal_()
        eps = eps.type_as(mu)

        return eps.mul(std).add_(mu)

    def forward(self, x: Tensor) -> Tuple[Tensor, Tensor, Tensor]:
        mu, logvar = self.encoder(x)
        z = self.reparametrize(mu, logvar)
        decoded = self.decoder(z)
        return decoded, mu, logvar

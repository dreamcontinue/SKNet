import torch
import torch.nn as nn


class Bottleneck(nn.Module):
    def __init__(self, in_channels, mid_channels, out_channels, stride=1):
        super(Bottleneck, self).__init__()
        self.conv1 = nn.Sequential(
            nn.Conv2d(in_channels, mid_channels, kernel_size=1, stride=1, bias=False),
            nn.BatchNorm2d(mid_channels),
            nn.ReLU(inplace=True)
        )
        self.conv2 = nn.Sequential(
            nn.Conv2d(mid_channels, mid_channels, kernel_size=3, stride=stride, padding=1, bias=False),
            nn.BatchNorm2d(mid_channels),
            nn.ReLU(inplace=True)
        )
        self.conv3 = nn.Sequential(
            nn.Conv2d(mid_channels, out_channels, kernel_size=1, stride=1, bias=False),
            nn.BatchNorm2d(out_channels)
        )

        if in_channels == out_channels:  # when dim not change, input_features could be added diectly to out
            self.shortcut = nn.Sequential()
        else:  # when dim change, input_features should also change dim to be added to out
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels)
            )
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        residual = x
        residual = self.shortcut(residual)

        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x += residual

        return self.relu(x)


class resnet(nn.Module):
    def __init__(self, num_classes, num_block_lists=[3, 4, 6, 3]):
        super(resnet, self).__init__()
        self.basic_conv = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        )

        self.stage_1 = self._make_layer(64, 64, 256, nums_block=num_block_lists[0], stride=1)
        self.stage_2 = self._make_layer(256, 128, 512, nums_block=num_block_lists[1], stride=2)
        self.stage_3 = self._make_layer(512, 256, 1024, nums_block=num_block_lists[2], stride=2)
        self.stage_4 = self._make_layer(1024, 512, 2048, nums_block=num_block_lists[3], stride=2)

        self.gap = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Linear(2048, num_classes)

        for m in self.modules():
            if isinstance(m, (nn.Conv2d, nn.Linear)):
                nn.init.kaiming_normal_(m.weight, mode='fan_in')
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.ones_(m.weight)
                nn.init.zeros_(m.bias)

    def _make_layer(self, in_channels, mid_channels, out_channels, nums_block, stride=1):
        layers = [Bottleneck(in_channels, mid_channels, out_channels, stride=stride)]
        for _ in range(1, nums_block):
            layers.append(Bottleneck(out_channels, mid_channels, out_channels))
        return nn.Sequential(*layers)

    def forward(self, x):
        x = self.basic_conv(x)
        x = self.stage_1(x)
        x = self.stage_2(x)
        x = self.stage_3(x)
        x = self.stage_4(x)
        x = self.gap(x)
        x = x.view(x.size(0), -1)

        x = self.classifier(x)
        return x


def ResNet(num_classes=1000, depth=50):
    assert depth in [50, 101, 152], 'depth invalid'
    key2blocks = {
        50: [3, 4, 6, 3],
        101: [3, 4, 23, 3],
    }
    model = resnet(num_classes, key2blocks[depth])
    return model


if __name__ == '__main__':
    batch = 2
    inplanes = 3
    outplanes = 1000
    h, w = 224, 224

    model = ResNet(outplanes, depth=50)
    x = torch.rand((batch, inplanes, h, w))
    model(x)
    print(model)

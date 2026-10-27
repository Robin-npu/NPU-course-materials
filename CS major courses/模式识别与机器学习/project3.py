import time
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Subset

from torchvision import datasets, transforms


# 1. 固定随机种子
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


set_seed(42)


# 2. 设备选择
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print("Using device:", device)


# 3. 数据集加载与 10% 采样
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.1307,), (0.3081,))
])


train_dataset = datasets.MNIST(
    root="mycode\ML\mnist_jpg",
    train=True,
    download=True,
    transform=transform
)

test_dataset = datasets.MNIST(
    root="mycode\ML\mnist_jpg",
    train=False,
    download=True,
    transform=transform
)


def stratified_subset(dataset, fraction=0.1, seed=42):
    """
    按类别分层抽样，保证 0-9 每一类都抽取相同比例的数据。
    MNIST 训练集 60000 张，10% 为 6000 张；
    MNIST 测试集 10000 张，10% 为 1000 张。
    """
    rng = np.random.default_rng(seed)

    targets = np.array(dataset.targets)
    selected_indices = []

    for cls in range(10):
        cls_indices = np.where(targets == cls)[0]
        n_select = int(len(cls_indices) * fraction)
        chosen = rng.choice(cls_indices, size=n_select, replace=False)
        selected_indices.extend(chosen.tolist())

    rng.shuffle(selected_indices)
    return Subset(dataset, selected_indices)


train_subset = stratified_subset(train_dataset, fraction=0.1, seed=42)
test_subset = stratified_subset(test_dataset, fraction=0.1, seed=42)

batch_size = 64

train_loader = DataLoader(
    train_subset,
    batch_size=batch_size,
    shuffle=True
)

test_loader = DataLoader(
    test_subset,
    batch_size=batch_size,
    shuffle=False
)

print("Train samples:", len(train_subset))
print("Test samples:", len(test_subset))


# 4. MLP 模型定义
class MLP(nn.Module):
    def __init__(self):
        super(MLP, self).__init__()

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(28 * 28, 256),
            nn.ReLU(),
            nn.Dropout(0.2),

            nn.Linear(256, 128),
            nn.ReLU(),

            nn.Linear(128, 10)
        )

    def forward(self, x):
        return self.classifier(x)


# 5. CNN 模型定义
class SimpleCNN(nn.Module):
    def __init__(self):
        super(SimpleCNN, self).__init__()

        self.features = nn.Sequential(
            nn.Conv2d(1, 8, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2),

            nn.Conv2d(8, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2)
        )

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(16 * 7 * 7, 10)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x


# 6. 参数量统计函数
def count_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


# 7. 测试/验证函数
def evaluate(model, data_loader):
    model.eval()

    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in data_loader:
            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)
            preds = torch.argmax(outputs, dim=1)

            correct += (preds == labels).sum().item()
            total += labels.size(0)

    acc = correct / total
    return acc


# 8. 训练函数
def train_model(model, train_loader, test_loader, epochs=5, lr=1e-3):
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)

    train_losses = []
    val_accuracies = []

    start_time = time.time()

    for epoch in range(epochs):
        model.train()

        running_loss = 0.0
        total_samples = 0

        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()

            outputs = model(images)
            loss = criterion(outputs, labels)

            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            total_samples += images.size(0)

        avg_loss = running_loss / total_samples
        val_acc = evaluate(model, test_loader)

        train_losses.append(avg_loss)
        val_accuracies.append(val_acc)

        print(
            f"Epoch [{epoch + 1}/{epochs}] "
            f"Loss: {avg_loss:.4f} "
            f"Val/Test Acc: {val_acc:.4f}"
        )

    end_time = time.time()
    total_time = end_time - start_time

    return train_losses, val_accuracies, total_time


# 9. 训练 MLP 与 CNN
epochs = 5
lr = 1e-3

mlp = MLP()
cnn = SimpleCNN()

mlp_params = count_parameters(mlp)
cnn_params = count_parameters(cnn)

print("\nMLP parameters:", mlp_params)
print("CNN parameters:", cnn_params)

print("\nTraining MLP...")
mlp_losses, mlp_accs, mlp_time = train_model(
    mlp,
    train_loader,
    test_loader,
    epochs=epochs,
    lr=lr
)

print("\nTraining CNN...")
cnn_losses, cnn_accs, cnn_time = train_model(
    cnn,
    train_loader,
    test_loader,
    epochs=epochs,
    lr=lr
)


# 10. 保存实验结果
results = pd.DataFrame({
    "Model": ["MLP", "CNN"],
    "Parameters": [mlp_params, cnn_params],
    "Training Time (s)": [mlp_time, cnn_time],
    "Final Accuracy": [mlp_accs[-1], cnn_accs[-1]]
})

print("\nExperimental Results:")
print(results)

results.to_csv("mnist_mlp_cnn_results.csv", index=False, encoding="utf-8-sig")


# 11. 绘制训练损失曲线
plt.figure(figsize=(8, 5))
plt.plot(range(1, epochs + 1), mlp_losses, marker="o", label="MLP Training Loss")
plt.plot(range(1, epochs + 1), cnn_losses, marker="s", label="CNN Training Loss")
plt.xlabel("Epoch")
plt.ylabel("Training Loss")
plt.title("Training Loss Comparison between MLP and CNN")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("training_loss_comparison.png", dpi=300)
plt.show()

# 12. 绘制验证/测试准确率曲线
plt.figure(figsize=(8, 5))
plt.plot(range(1, epochs + 1), mlp_accs, marker="o", label="MLP Validation/Test Accuracy")
plt.plot(range(1, epochs + 1), cnn_accs, marker="s", label="CNN Validation/Test Accuracy")
plt.xlabel("Epoch")
plt.ylabel("Accuracy")
plt.title("Validation/Test Accuracy Comparison between MLP and CNN")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("accuracy_comparison.png", dpi=300)
plt.show()


# 13. 选做：可视化 CNN 第一层卷积特征图
def visualize_cnn_feature_maps(model, data_loader, save_path="cnn_feature_maps.png"):
    model.eval()

    images, labels = next(iter(data_loader))
    image = images[0:1].to(device)
    label = labels[0].item()

    with torch.no_grad():
        conv1 = model.features[0]
        feature_maps = conv1(image)
        feature_maps = feature_maps.cpu().squeeze(0)

    plt.figure(figsize=(10, 4))

    plt.subplot(2, 5, 1)
    plt.imshow(image.cpu().squeeze(), cmap="gray")
    plt.title(f"Input: {label}")
    plt.axis("off")

    for i in range(min(8, feature_maps.shape[0])):
        plt.subplot(2, 5, i + 2)
        plt.imshow(feature_maps[i], cmap="gray")
        plt.title(f"Map {i + 1}")
        plt.axis("off")

    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.show()


visualize_cnn_feature_maps(cnn, test_loader)
import torch
import torchvision
from torchvision import transforms
import torch.nn as nn
import torch.optim as optim

# 1. 🚀 DATA AUGMENTATION: Flips, rotates, and shifts colors to artificially expand your dataset
data_transforms = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(15),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

# 2. Load the Dataset
try:
    dataset = torchvision.datasets.ImageFolder('product_images/dataset', data_transforms)
    dataloader = torch.utils.data.DataLoader(dataset, batch_size=4, shuffle=True)
    print(f"✅ Data loaded successfully! Found {len(dataset)} images.")
    print(f"✅ Classes detected: {dataset.classes}")
except Exception as e:
    print(f"❌ Error loading data: Make sure your images are inside subfolders in media/dataset/. Error: {e}")
    exit()

# 3. Load Pre-trained MobileNetV2 (Transfer Learning)
model = torchvision.models.mobilenet_v2(weights='DEFAULT')

# Freeze the base layers so we don't destroy the pre-trained vision weights
for param in model.parameters():
    param.requires_grad = False

# Unfreeze and replace ONLY the final classification layer to match your 5 classes
num_features = model.classifier[1].in_features
model.classifier[1] = nn.Linear(num_features, len(dataset.classes))

# 4. Define Loss and Optimizer
criterion = nn.CrossEntropyLoss()
# We only optimize the final layer we just created
optimizer = optim.Adam(model.classifier[1].parameters(), lr=0.001)

# 5. The Training Loop
epochs = 15
print(f"🚀 Starting training for {epochs} epochs...")

model.train()
for epoch in range(epochs):
    running_loss = 0.0
    for inputs, labels in dataloader:
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item()
        
    avg_loss = running_loss / len(dataloader)
    print(f"Epoch [{epoch+1}/{epochs}] - Loss: {avg_loss:.4f}")

# 6. Export the Model for Django
# We use TorchScript to export it, which makes it much easier to load into views.py later!
model.eval()
example_input = torch.rand(1, 3, 224, 224)
traced_script_module = torch.jit.trace(model, example_input)
traced_script_module.save("skin_model.pt")

print("🎉 Training Complete! Model saved as 'skin_model.pt'")
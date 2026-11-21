from torch.nn import LSTM, Linear, Module, CrossEntropyLoss
from torch.utils.data import TensorDataset, DataLoader
import torch
import torch.nn.functional as F
import matplotlib.pyplot as plt
from tqdm import tqdm


class AutoEncoder(Module):
    def __init__(self,cities=20,hs=64):
        super(AutoEncoder,self).__init__()
        self.encoder=LSTM(cities,hs,batch_first=True)
        self.attention=Linear(hs,1)
        self.decoder=LSTM(hs,hs,batch_first=True)
        self.fc=Linear(hs,cities)

    def forward(self, x): 
        encoder_output, (h_n,c_n)=self.encoder(x)
        attn_weights = F.softmax(self.attention(encoder_output), dim=1) 
        context = encoder_output * attn_weights
        decoder_outputs, __ = self.decoder(context, (h_n, c_n))
        return self.fc(decoder_outputs)
        #return F.softmax(logits, dim=-1)







def train_model(paths, epochs=1000, lr=1e-3, cities=20, hs=64, save_path="autoencoder_aco.pt",loss_plot_path="loss_curve.png"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    X = torch.stack(paths)
    Y = X.argmax(dim=-1).long()
    dataset = TensorDataset(X, Y)
    loader = DataLoader(dataset, batch_size=64, shuffle=True)
    model = AutoEncoder(cities=cities, hs=hs).to(device)
    criterion = CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_history = []
    for epoch in tqdm(range(1, epochs + 1)):
        model.train()
        total_loss = 0.0
        for batch_x, batch_y in loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            optimizer.zero_grad()
            logits = model(batch_x)
            loss = criterion(logits.transpose(1, 2), batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        avg_loss = total_loss / len(loader)
        loss_history.append(avg_loss)
        if epoch % 10 == 0 or epoch == 1:
            print(f"Época {epoch}/{epochs} - Loss: {avg_loss:.4f}")
    torch.save(model.state_dict(), save_path)
    print(f"Modelo salvo em: {save_path}")
    plt.figure(figsize=(8, 4))
    plt.plot(range(1, epochs + 1), loss_history, marker="o", markersize=3)
    plt.title("Curva de Perda no Treino")
    plt.xlabel("Época")
    plt.ylabel("Loss")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(loss_plot_path, dpi=150)
    plt.close()
    print(f"Gráfico de perda salvo em: {loss_plot_path}")
    return model
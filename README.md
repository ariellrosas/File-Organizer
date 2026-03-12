# 📁 File Organizer — Organizador Automático de Arquivos

> **EN:** A desktop application for Windows that automatically monitors folders and moves files based on keyword rules — with a graphical interface and system tray support.
>
> **PT:** Aplicativo desktop para Windows que monitora pastas automaticamente e move arquivos com base em regras de palavras-chave — com interface gráfica e suporte à bandeja do sistema.

---

## 🇧🇷 Português

### Sobre o Projeto

O **File Organizer** é um aplicativo desktop desenvolvido em Python com interface gráfica PyQt5. Ele monitora pastas em segundo plano e move arquivos automaticamente para os destinos configurados sempre que detecta um arquivo cujo nome contém uma palavra-chave definida pelo usuário.

O aplicativo roda discretamente na bandeja do sistema (system tray) e persiste entre reinicializações, retomando o monitoramento automaticamente se estava ativo ao ser fechado.

### Funcionalidades

- ✅ Monitoramento contínuo de múltiplas pastas em segundo plano
- ✅ Regras configuráveis por palavra-chave (ex: mover todos os arquivos com "fatura" para a pasta Finanças)
- ✅ Interface gráfica intuitiva com tabela de regras
- ✅ Ícone na bandeja do sistema — fechar a janela não encerra o aplicativo
- ✅ Log de atividades em tempo real
- ✅ Persistência de configuração via `config.json`
- ✅ Proteção contra sobrescrita de arquivos (renomeia automaticamente com sufixo numérico)
- ✅ Criação automática da pasta de destino caso não exista

### Pré-requisitos

- Windows 10 ou superior
- Python 3.8+
- pip

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/file-organizer.git
cd file-organizer

# 2. Instale as dependências
pip install PyQt5
```

### Como Usar

```bash
python app_organizador.py
```

1. Clique em **➕ Adicionar Regra**
2. Selecione a **pasta a ser monitorada**
3. Digite uma **palavra-chave** (ex: `fatura`, `imagem`, `relatorio`)
4. Selecione a **pasta de destino**
5. Clique em **▶️ Iniciar Monitoramento**

O aplicativo passará a verificar a pasta a cada 2 segundos. Ao detectar um arquivo cujo nome contenha a palavra-chave, ele será movido automaticamente para a pasta de destino.

> 💡 **Dica:** Ao fechar a janela, o aplicativo continua rodando na bandeja. Para encerrar completamente, clique com o botão direito no ícone da bandeja e selecione **Sair**.

### Estrutura do Projeto

```
file-organizer/
├── app_organizador.py   # Código principal do aplicativo
└── config.json          # Gerado automaticamente ao salvar regras
```

### Arquivo de Configuração

O `config.json` é gerado automaticamente e armazena as regras e o estado do monitoramento:

```json
{
  "rules": [
    {
      "watch_folder": "C:/Users/usuario/Downloads",
      "keyword": "fatura",
      "target_folder": "C:/Users/usuario/Documentos/Faturas",
      "enabled": true
    }
  ],
  "interval": 2,
  "monitoring_enabled": true
}
```

### Gerando o Executável (.exe)

Para distribuir o aplicativo sem precisar do Python instalado, use o **PyInstaller**:

```bash
# 1. Instale o PyInstaller
pip install pyinstaller

# 2. Gere o executável
pyinstaller --onefile --windowed --name "FileOrganizer" app_organizador.py
```

O arquivo `FileOrganizer.exe` será gerado dentro da pasta `dist/`.

| Flag | Descrição |
|------|-----------|
| `--onefile` | Empacota tudo em um único `.exe` |
| `--windowed` | Não abre janela de terminal ao executar |
| `--name` | Define o nome do executável gerado |

> ⚠️ **Atenção:** O `config.json` será criado na mesma pasta onde o `.exe` for executado. Mantenha ambos no mesmo diretório.

---

## 🇺🇸 English

### About

**File Organizer** is a Windows desktop application built with Python and PyQt5. It monitors folders in the background and automatically moves files to configured destinations whenever a file name contains a user-defined keyword.

The app runs quietly in the system tray and persists between restarts, automatically resuming monitoring if it was active when last closed.

### Features

- ✅ Continuous background monitoring of multiple folders
- ✅ Keyword-based rules (e.g. move all files containing "invoice" to the Finance folder)
- ✅ Intuitive GUI with a rules table
- ✅ System tray icon — closing the window does not quit the app
- ✅ Real-time activity log
- ✅ Configuration persistence via `config.json`
- ✅ File overwrite protection (auto-renames with numeric suffix)
- ✅ Automatic creation of destination folder if it doesn't exist

### Requirements

- Windows 10 or later
- Python 3.8+
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/seu-usuario/file-organizer.git
cd file-organizer

# 2. Install dependencies
pip install PyQt5
```

### Usage

```bash
python app_organizador.py
```

1. Click **➕ Add Rule**
2. Select the **folder to monitor**
3. Enter a **keyword** (e.g. `invoice`, `image`, `report`)
4. Select the **destination folder**
5. Click **▶️ Start Monitoring**

The app checks the folder every 2 seconds. When a file whose name contains the keyword is detected, it is automatically moved to the destination folder.

> 💡 **Tip:** Closing the window keeps the app running in the system tray. To fully quit, right-click the tray icon and select **Quit**.

### Project Structure

```
file-organizer/
├── app_organizador.py   # Main application code
└── config.json          # Auto-generated when rules are saved
```

### Configuration File

`config.json` is auto-generated and stores rules and monitoring state:

```json
{
  "rules": [
    {
      "watch_folder": "C:/Users/user/Downloads",
      "keyword": "invoice",
      "target_folder": "C:/Users/user/Documents/Invoices",
      "enabled": true
    }
  ],
  "interval": 2,
  "monitoring_enabled": true
}
```

### Building the Executable (.exe)

To distribute the app without requiring Python to be installed, use **PyInstaller**:

```bash
# 1. Install PyInstaller
pip install pyinstaller

# 2. Build the executable
pyinstaller --onefile --windowed --name "FileOrganizer" app_organizador.py
```

The `FileOrganizer.exe` file will be generated inside the `dist/` folder.

| Flag | Description |
|------|-------------|
| `--onefile` | Bundles everything into a single `.exe` |
| `--windowed` | Suppresses the terminal window on launch |
| `--name` | Sets the name of the generated executable |

> ⚠️ **Note:** The `config.json` will be created in the same folder where the `.exe` is run. Keep both files in the same directory.

---

## 🛠️ Tech Stack

| | |
|---|---|
| Language | Python 3.8+ |
| GUI Framework | PyQt5 |
| Threading | Python `threading` |
| Config | JSON |
| Platform | Windows |

---

*Desenvolvido com Python e PyQt5 · Built with Python and PyQt5*

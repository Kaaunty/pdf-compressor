# PDF Compressor

Um aplicativo web moderno, elegante e de alta performance para compactação de arquivos PDF. Todo o processamento é feito **100% localmente no seu computador**, garantindo total privacidade e segurança dos seus dados, sem que nenhum arquivo seja enviado para a nuvem.

---

## 🚀 Funcionalidades

- **Compactação Inteligente:**
  - Otimização e compressão de streams internos do PDF.
  - Limpeza de estruturas redundantes e objetos órfãos através de coleta de lixo profunda (Garbage Collection nível 4).
  - Otimização automática de imagens incorporadas (redimensionamento e re-codificação de qualidade).
  - Preservação inteligente de transparência (mantém assinaturas e logotipos pequenos em PNG transparente e converte fotos/imagens grandes para JPEG comprimido).
- **Ajustes Customizados:**
  - Três níveis de presets: **Alta Qualidade** (compressão leve), **Balanceado** (recomendado) e **Tamanho Mínimo** (agressivo).
  - Sliders manuais de qualidade e escala (resolução) das imagens.
  - Opção de conversão para **Tons de Cinza** (grayscale) para economizar ainda mais espaço.
  - Opção de remoção de metadados (título, autor, criador, datas).
- **Experiência de Usuário Premium:**
  - Interface moderna em **Dark Mode** com design em Glassmorphism, brilhos ambientes e micro-animações suaves.
  - **Progresso Realista em Tempo Real:** Exibe a porcentagem real da compressão e o status detalhado da operação (ex: *"Otimizando imagem 2 de 5... (40%)"*).
  - Upload via Drag & Drop ou clique.
- **Gerenciamento Seguro de Disco:**
  - O arquivo original enviado é deletado assim que a compressão inicia.
  - O arquivo compactado gerado é **excluído automaticamente** do servidor imediatamente após o término do download do usuário.

---

## 🛠️ Arquitetura do Projeto

A aplicação é dividida de forma modular:

*   **Backend (Python + FastAPI):** Gerencia as rotas da API, coordena a execução em threads em segundo plano (evitando bloqueios no servidor) e serve a interface estática.
*   **Motor de Otimização (PyMuPDF + Pillow):** O `PyMuPDF` lida com a leitura, reestruturação interna e escrita do PDF, enquanto a biblioteca `Pillow` é responsável pelo redimensionamento e re-compressão de imagem.
*   **Frontend (HTML5 + CSS3 + Vanilla Javascript):** Construído sem frameworks pesados, garantindo carregamento instantâneo. Utiliza a biblioteca Lucide para ícones e faz consultas periódicas (polling) ao backend para atualizar o progresso realístico.

---

## 📦 Estrutura de Arquivos

```
fearless-darwin/
├── main.py               # Servidor FastAPI e controle de endpoints/background tasks
├── pdf_compressor.py     # Lógica central de compactação (PyMuPDF & Pillow)
├── requirements.txt      # Dependências de bibliotecas Python
├── run.bat               # Script automatizado de inicialização para Windows
├── Dockerfile            # Configuração de container Docker
├── docker-compose.yml    # Orquestração do container Docker
├── .gitignore            # Ignora pastas de ambiente virtual, temp e caches
└── static/               # Assets e interface do Frontend
    ├── index.html        # Página principal e estrutura da UI
    ├── index.css         # Estilização visual (Glassmorphism & Dark Mode)
    └── index.js          # Controlador JS (interações de tela e consumo da API)
```

---

## ⚙️ Como Executar a Aplicação

Existem três formas fáceis de rodar o compactador no seu computador:

### Opção 1: Atalho de Script para Windows (Recomendado)
Se você estiver no Windows, basta dar dois cliques no arquivo:
1. Vá até o diretório do projeto e dê dois cliques em **`run.bat`**.
2. O script irá criar um ambiente virtual Python (`.venv`), instalar as dependências necessárias, iniciar o servidor local e abrir automaticamente a interface no seu navegador padrão em `http://127.0.0.1:8000`.

### Opção 2: Utilizando Docker (Containerizado)
Se você utiliza Docker, pode rodar o projeto de forma isolada com o comando:
```bash
docker compose up --build
```
Após o build e a inicialização, abra o navegador e acesse **`http://127.0.0.1:8000`**.

### Opção 3: Execução Manual (Qualquer SO)
Caso queira rodar manualmente pelo terminal:
1. Crie e ative um ambiente virtual:
   ```bash
   python -m venv .venv
   # No Windows:
   .venv\Scripts\activate
   # No Linux/Mac:
   source .venv/bin/activate
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Execute o servidor:
   ```bash
   python main.py
   ```
4. Acesse **`http://127.0.0.1:8000`** no seu navegador.

---

## 📜 Licença

Este projeto é de uso livre e sob a licença [MIT](LICENSE). Sinta-se à vontade para utilizar, modificar e distribuir.

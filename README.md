# Classificador de Tickets com LLM (Ollama)

Aplicação web simples para carregar um CSV/XLSX com **número do ticket, descrição, data e autor** e receber uma classificação automática baseada em uma LLM open source (Llama via Ollama).

## ✅ Pré-requisitos

- Docker
- Docker Compose

## 🚀 Como subir com Docker (passo a passo)

1. **Clone o repositório**
   ```bash
   git clone <URL_DO_SEU_REPOSITORIO>
   cd app_ticket_classificador
   ```

2. **Suba tudo com um único comando**
   ```bash
   docker-compose up --build
   ```

3. **Acesse no navegador**
   - http://localhost:8000

O Docker Compose sobe apenas a aplicação web. Garanta que sua instância do Ollama esteja rodando separadamente (ex: em `http://localhost:11434`).

4. **Faça o mapeamento das colunas**
   - Após enviar o CSV/XLSX, selecione quais colunas do arquivo correspondem a **ticket, descrição, data e autor**.
   - Caso seu Ollama esteja rodando localmente fora do Docker, informe a URL no campo **URL do Ollama**.

## 📄 Formato do arquivo

O CSV/XLSX precisa ter as seguintes colunas (podem estar em minúsculo ou com acentos):

- número do ticket
- descrição
- data
- autor

## ⚙️ Como funciona a classificação

- A aplicação envia a **descrição** de cada ticket para o Ollama.
- A LLM retorna um JSON com duas chaves:
  - `acao` → ação recomendada para o ticket
  - `grupo` → rótulo para agrupar tickets similares

## 🧩 Solução de problemas

- **Erro ao classificar (Ollama 404/indisponível):** verifique se o Ollama está rodando na URL configurada (campo **URL do Ollama**) e se o modelo foi baixado na sua instância.

## 🧠 Trocar o modelo

Se você quiser usar outro modelo, basta editar a variável no formulário da tela inicial ou alterar no `docker-compose.yml`:

```yaml
environment:
  OLLAMA_MODEL: llama3.1
```

## 📂 Estrutura

```
.
├── app/
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── templates/
│   └── static/
├── docker-compose.yml
└── README.md
```

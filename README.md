# Aula 8 — Text-to-SQL com SQLAlchemy, Ollama e PostgreSQL

Projeto didático que transforma perguntas em português em consultas SQL para
uma locadora. A aplicação descobre o esquema do PostgreSQL com SQLAlchemy e
organiza o fluxo em três agentes:

1. **Planejador:** usa o esquema do banco e o histórico da conversa para propor
   uma consulta SQL.
2. **Executor:** valida a consulta com SQLGlot e executa somente SQL autorizada.
3. **Interpretador:** apresenta os resultados reais em português.

O executor é determinístico e não usa uma segunda LLM. A memória existe apenas
durante a execução do programa e guarda até cinco interações bem-sucedidas.

## Pré-requisitos

- Python 3.10 ou superior;
- PostgreSQL com a base didática da locadora importada;
- usuário PostgreSQL com permissão somente de leitura;
- [Ollama](https://ollama.com/) instalado;
- modelo `qwen2.5:3b` disponível no Ollama.

Baixe o modelo, caso ainda não esteja instalado:

```bash
ollama pull qwen2.5:3b
```

## Instalação

No macOS ou Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

No Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Configuração

Crie o arquivo local de configuração a partir do exemplo:

```bash
cp .env.example .env
```

No Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Preencha o `.env` com as credenciais do PostgreSQL e, se necessário, altere a
URL ou o modelo do Ollama. O arquivo `.env` está ignorado pelo Git e não deve
ser enviado ao GitHub.

## Execução

Para inspecionar tabelas, colunas e relacionamentos do banco:

```bash
python explorar_banco.py
```

Para executar o exemplo introdutório, com uma chamada ao modelo:

```bash
python 02_perguntar_banco.py
```

Para iniciar o fluxo completo com três agentes, autocorreção e memória de
sessão:

```bash
python 03_tres_agentes.py
```

Durante a conversa, digite `limpar` para apagar a memória da sessão ou `sair`
para encerrar.

Perguntas sugeridas:

- Quantos clientes existem na locadora?
- Quais são os cinco modelos de veículos mais alugados?
- Quais filiais possuem mais locações concluídas?
- Qual é o total de pagamentos com status pago?
- Desses modelos, qual teve maior receita?

## Estrutura do projeto

```text
.
├── .env.example              # modelo das variáveis locais
├── .gitignore
├── README.md
├── requirements.txt
├── explorar_banco.py         # inspeciona o banco didático
├── 02_perguntar_banco.py     # exemplo introdutório de Text-to-SQL
├── 03_tres_agentes.py        # ponto de entrada da aplicação completa
├── configuracao.py           # conexão e descoberta do esquema
├── ollama.py                 # cliente HTTP local do Ollama
├── agente_planejador.py      # geração e correção da consulta
├── agente_executor.py        # validação e execução controlada
├── agente_interpretador.py   # explicação dos resultados
└── memoria.py                # memória temporária da conversa
```

## Segurança e limitações

- Use obrigatoriamente uma conta PostgreSQL com permissão somente de leitura.
- As consultas rodam em transação `READ ONLY`, com timeout de cinco segundos e
  limite externo de 20 linhas.
- SQLGlot ajuda a validar a estrutura da consulta, mas não substitui as
  permissões configuradas no banco.
- O planejador pode errar relacionamentos ou critérios de negócio; confira a
  SQL e os resultados antes de confiar na resposta final.
- A memória não é persistida: ela é apagada quando o programa termina.

## Atividade sugerida

Faça uma pergunta de contagem, uma com relacionamento entre tabelas e uma com
agregação. Para cada uma, registre a SQL proposta, o número de linhas retornado
e a resposta final. Depois, descreva um caso em que a consulta precisou de
autocorreção ou foi bloqueada pelo executor.

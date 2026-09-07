# SaaS Log

> Plataforma SaaS para coleta, correlação e monitoramento de logs em aplicações distribuídas — projetada para facilitar investigação de incidentes, alertas em tempo real e análise de performance.

[Badges: build / tests / coverage / license]<!-- substitua pelos badges reais -->

Sumário
- Status: Em desenvolvimento / Produção (escolha)
- Linguagens/Stack: Python, Streamlit, DuckDB, Pandas, NumPy, Airflow, PostgreSQL (exemplo)
- Repo: https://github.com/Sharkduh/SaaS_Log
- Demo: https://saaslog-7mcmjegfg6hrkcm8eonm2p.streamlit.app/
- Docs adicionais: docs/

Visão geral
------------
SaaS Log centraliza logs de múltiplos serviços, fornece busca e correlação rápida por request/trace id, e entrega dashboards e alertas configuráveis para reduzir o MTTR (Mean Time To Recovery) em ambientes distribuídos.

Problema que resolve
--------------------
- Logs dispersos entre serviços dificultam investigações.
- Necessidade de correlação de eventos e visão de linhagem de dados.
- Solução acessível para startups e PMEs com deploy serverless disponível.

Principais funcionalidades
--------------------------
- Ingestão via SDK/agent (HTTP, gRPC, syslog).
- Busca full-text e filtros por serviço, ambiente, trace id e timeframe.
- Correlation view por request/trace id.
- Dashboards interativos e indicadores (painéis de indicadores e séries temporais).
- Alertas e integrações: Slack, e-mail, PagerDuty, webhooks.
- Retenção configurável, exportação e políticas multi-tenant.
- Observabilidade e tracing (OpenTelemetry).

Infraestrutura e Orquestração
-----------------------------
- Apache Airflow 3: motor de orquestração e agendamento cron da DAG `fulfillment_last_mile_pipeline`; garante monitoramento da integridade das esteiras e definição de data lineage.
- Git & GitHub: controle de versão e portfólio público (https://github.com/Sharkduh/SaaS_Log).
- Streamlit Community Cloud: hospedagem serverless da aplicação web com link público seguro via HTTPS para demonstrações e PoC (https://saaslog-7mcmjegfg6hrkcm8eonm2p.streamlit.app/).

Motores de Processamento e Bancos de Dados
------------------------------------------
- DuckDB (Camada Gold): OLAP em memória de alta performance para queries analíticas, agregações e uso de TRY_CAST para conversões seguras.
- Pandas (Camada Silver): Data cleansing e transformação vetorizada; cálculos de lead time entre timestamps e conversões dinâmicas de tipos.
- NumPy: geração de matrizes e distribuições probabilísticas simuladas (np.random.seed) para testes e simulações.

Front-end e Visualização de Dados
--------------------------------
- Streamlit Framework: interface interativa construída em Python, sem necessidade de HTML/CSS tradicionais.
- Plotly Graph Objects: gráficos interativos de alta precisão (indicadores, séries temporais e painéis).
- CSS Injection via `st.markdown`: tema Dark Premium com cartões corporativos e estilização customizada.

Suporte e Conectores de Arquivos
--------------------------------
- openpyxl: leitura de planilhas Excel (.xlsx) integradas ao pipeline via Pandas.
- Leitor CSV (engine nativa): suporte a CSV com vírgula/ponto e vírgula e mapeamento robusto de colunas.
- Bibliotecas `os` & `sys` (stdlib): manipulação de caminhos e diretórios das camadas data/bronze, data/silver, data/gold em ambiente Linux/container.

Qualidade de Software e Testes
------------------------------
- Pytest: suíte de testes automatizados (unitários e de integração) para validação de regras de negócio e pipelines; previne regressões em deploys.

Inteligência de Produto (Mapeamento Agnóstico)
----------------------------------------------
- Matriz Dinâmica de Sinônimos: algoritmo em Python para normalizar títulos de colunas (`strip`, mapeamento por sinônimos) e transformar qualquer planilha logística em chaves universais do sistema.

Arquitetura & Stack (resumo)
----------------------------
- Backend: Python (ETL, API leve)
- Orquestração: Apache Airflow 3 (DAG: `fulfillment_last_mile_pipeline`)
- Processing: Pandas, DuckDB, NumPy
- Frontend: Streamlit + Plotly
- Storage: PostgreSQL (metadados) + object storage (S3) para logs brutos
- CI/CD: GitHub Actions → deploy para Streamlit Community Cloud / Container registry
- Observability: Prometheus + Grafana (opcional), OpenTelemetry

Instalação rápida (local)
-------------------------
Requisitos: Python 3.10+, pip, Docker (opcional)

1. Clone:
   git clone https://github.com/Sharkduh/SaaS_Log.git
   cd SaaS_Log

2. Virtualenv e dependências:
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt

3. Variáveis de ambiente:
   cp .env.example .env
   # Edite .env conforme necessário (DATABASE_URL, STREAMLIT_SERVER_PORT, etc.)

4. Rodar Streamlit localmente:
   streamlit run app.py

5. Rodar DuckDB (ex.: shell ou integrado no app) e Airflow local (opcional/baseline via Docker Compose):
   docker compose up --build

Execução e deploy no Streamlit Community Cloud
----------------------------------------------
- Repositório: https://github.com/Sharkduh/SaaS_Log
- Link do deploy público: https://saaslog-7mcmjegfg6hrkcm8eonm2p.streamlit.app/
- Conecte o repositório no Streamlit Community Cloud e configure variáveis de ambiente; push na branch principal → deploy automático.

Testes
------
- Unitários: pytest tests/unit
- Integração: pytest tests/integration
- Coverage: pytest --cov=saas_log

Como apresentar este projeto a recrutadores (script curto)
---------------------------------------------------------
Elevator pitch (1 frase): "SaaS Log é uma plataforma que centraliza e correlaciona logs em ambientes distribuídos, reduzindo significativamente o tempo de resolução de incidentes."

Tópicos para destacar durante a entrevista:
- Problema + impacto (ex.: redução esperada no MTTR).
- A arquitetura escolhida e trade-offs (por que DuckDB para OLAP; Airflow para orquestração).
- Sua contribuição técnica: design da DAG `fulfillment_last_mile_pipeline`, implementação do mapeamento agnóstico de colunas e otimização de queries analíticas.
- Escalabilidade: throughput/testes (ex.: X logs/s em simulação).
- Observabilidade e segurança (TLS, RBAC, retenção por tenant).
- Link para demo, screenshots e código no GitHub.

Pontos adicionais para o README
-------------------------------
- Adicione badges reais (build / tests / coverage / license).
- Inclua screenshots em docs/screenshots/ e GIFs em docs/gifs/.
- Preencha métricas reais (uptime, latência média, throughput) para aumentar impacto.

Contribuição
------------
1. Fork e crie uma branch feature/bugfix: git checkout -b feature/nome
2. Abra PR com descrição e checklist (tests, lint)
3. Siga o guia de estilo em CONTRIBUTING.md

Licença
-------
- MIT (substitua se necessário)

Contato
-------
- Autor: <Seu Nome> — GitHub: https://github.com/Sharkduh — Email: lion92185@gmail.com

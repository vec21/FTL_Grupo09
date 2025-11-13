# Implementaçãodo Projeto Tella (Django + ML)

## 1. Visão Geral
O Tella é implantado como um Web Service Python no Render, executando uma aplicação Django servida por Gunicorn. O modelo de ML (serializado em Joblib) é carregado de forma lazy no backend e utilizado para estimar o custo total de viagem com foco em turismo sustentável. A aplicação oferece interface web (HTML) e integra dados externos via RapidAPI (Google Places) para enriquecer destino, rating e fotos.

## 2. Serialização do Modelo
- Formato: `joblib` (arquivo `modelo_tella.joblib`).
- Local: mantido no repositório em `Tella_TurismoNacional/` (carregado por `core/ml.py` com fallback de path).
- Observação: o artefato atual não contém o pipeline completo de pré-processamento; o código garante que as features de entrada tenham os mesmos nomes/tipos usados no treino.
- Recomendações: versionar modelos (ex.: `modelo_tella_v1.joblib`) e manter `metrics.json` com RMSE/R² do treino/validação.

## 3. Serviço de Previsão (Aplicação)
- Framework: Django (`core/views.py`).
- Ponto de uso: ação de formulário no Planejador monta as features (categoria, preços médios ajustados por orçamento, sazonalidade, popularidade, fator de sustentabilidade, rating, latitude/longitude, etc.) e chama `estimate_cost` de `core/ml.py`.
- Cálculo: predição unitária multiplicada pelo número de dias informado pelo usuário.
- Observação: não há endpoint REST público de predição no MVP; a predição é acionada via fluxo web autenticado.

## 4. Integração de API Externa
- Fonte: RapidAPI (Google Places New V2) para busca de lugares, tipos, ratings e fotos.
- Segurança: chave via `RAPIDAPI_KEY` (ENV/Secret File), nunca no repositório.
- Performance: cache em memória (Django LocMemCache) com TTL configurável (`PLACES_CACHE_TTL`, padrão 600s). Timeout e tratamento de erro implementados nas views.

## 5. Segurança
- Configuração: `SECRET_KEY` em ENV/Secret File; `DEBUG=0` em produção; `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` preparados para `.onrender.com` e `RENDER_EXTERNAL_HOSTNAME`.
- Transporte: HTTPS terminado pelo Render.
- Acesso: páginas-chave atrás de autenticação Django (login obrigatório). CSRF habilitado.
- Segredos: `.env` ignorado por git; uso de Secret Files/Environment Variables no Render.

## 6. Monitoramento e Logs
- Logs: Django configurado com logging no console (nível ajustável por `LOG_LEVEL`). Registros incluem carregamento do modelo e chamadas de predição.
- Saúde/Disponibilidade: usar logs de aplicação no Render; opcional criar `/healthz` simples para checagem.
- Métricas: latência de resposta e taxa de erros pelos logs. Qualidade do modelo (MSE/R²) é avaliada offline; para produção futura, planeja-se coletar feedback do usuário para aferir acurácia.
- Alertas: durante o MVP, acompanhar manualmente os logs; em evolução, integrar monitor externo (ex.: UptimeRobot) ou webhooks.

## 7. Build & Deploy (Render)
- Arquivo: `render.yaml` (na raiz) com `rootDir: Tella_TurismoNacional/tella_project`.
- Build:
  - `pip install -r requirements.txt`
  - `python manage.py collectstatic --noinput`
  - `python manage.py migrate --noinput`
- Start: `gunicorn tella_project.wsgi:application`
- Ambiente: `PYTHON_VERSION=3.10.12`, `DJANGO_SETTINGS_MODULE=tella_project.settings`, `SECRET_KEY`, `DEBUG=0`, `RAPIDAPI_KEY`, `PLACES_CACHE_TTL` (opcional).
- Banco (MVP): SQLite (ephemeral em cada deploy). Para persistência, migrar para Postgres.

## 8. Banco de Dados
- MVP: SQLite (adequado para demonstração; dados e contas podem reiniciar a cada deploy). Criar superuser via shell do Render.
- Futuro: Postgres no Render; adicionar `psycopg2-binary` e configurar `DATABASE_URL` com `dj_database_url` no `settings.py`.

## 9. Riscos e Mitigações
- Cold start (plano Free): pode levar 20–60s sem tráfego. Mitigar com pré-aquecimento ou plano Always On.
- Intermitências da API externa: timeouts e falhas tratados com mensagens amigáveis e cache.
- Dataset reduzido: risco de overfitting; comunicar limitações e evoluir dataset.
- Desalinhamento de features: garantir nomes/tipos consistentes com o treino; em evolução, serializar pipeline completo.

## 10. Rollback e Versionamento
- Rollback: redeploy de commit anterior no Render.
- Versionar artefatos do modelo e documentar parâmetros/metricas no commit.


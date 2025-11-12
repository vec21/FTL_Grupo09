# Tella (Django)

## Requisitos
- Python 3.10+ (recomendado 3.10 ou 3.11)
- Pip actualizado
- (Opcional) Virtualenv / venv

## Preparação
```bash
# clonar e entrar no projeto
# git clone <URL_DO_REPOSITORIO>
cd FTL_Grupo09/Tella_TurismoNacional/tella_project

# criar e activar venv (Linux/macOS)
python -m venv .venv
source .venv/bin/activate

# Windows PowerShell
# python -m venv .venv
# .venv\Scripts\Activate.ps1

# instalar dependências
pip install -r ../requirements.txt

# migrar DB e iniciar
python manage.py migrate
python manage.py runserver
```
Aceder: http://127.0.0.1:8000/

## Estrutura Principal
```
tella_project/
  manage.py
  tella_project/
    settings.py
    urls.py
    wsgi.py / asgi.py
  core/
    views.py
    urls.py
    templates/core/*.html
static/
  (arquivos estáticos do projeto)
```

## Configuração por ambiente
Variáveis de ambiente suportadas (via .env ou Render):
- SECRET_KEY (obrigatória em produção)
- DEBUG ("1"/"0")
- ALLOWED_HOSTS (separado por vírgulas)
- RAPIDAPI_KEY (para Google Places via RapidAPI)
- PLACES_CACHE_TTL (opcional)

## Deploy no Render
O ficheiro `render.yaml` está na raiz do repositório e aponta para `Tella_TurismoNacional/tella_project`.
- Build: instala requirements e executa `collectstatic` (WhiteNoise serve os estáticos)
- Start: `gunicorn tella_project.wsgi:application`

Passos no Render:
1) Criar novo Web Service a partir do repositório
2) Confirmar rootDir conforme o `render.yaml`
3) Definir as env vars (SECRET_KEY, RAPIDAPI_KEY, DEBUG=0)

## Notas
- WhiteNoise e logging estruturado já configurados no `settings.py`.
- O modelo `modelo_tella.joblib` é carregado pelo módulo `core/ml.py`.



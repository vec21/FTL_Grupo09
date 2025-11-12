# Ntete Django Project

Projeto convertido de site estático para Django mantendo identidade visual.

## Requisitos
- Python 3.10+
- Django instalado (pip install django)

## Como iniciar
```bash
python manage.py migrate
python manage.py runserver
```

Acesse: http://127.0.0.1:8000/

## Estrutura
- core: app principal com templates
- static: arquivos CSS/JS/imagens
- templates/base.html: layout principal

## Próximo passo
Integrar ML no placeholder `#ml-result` da página Planejador.

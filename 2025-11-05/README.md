# 2025-11-05
Esta pasta contém os entregáveis para 2025-11-05: finalização e apresentação do projeto.

## Estrutura
- `docs/` - Documentação
- `data/` - Dados do projeto
- `notebooks/` - Jupyter notebooks
- `deliverables/` - Artefatos finais

## Entregáveis adicionados
- `Group09 Final Project.ipynb` — Notebook final com EDA, pré-processamento e treino do modelo.
- `destinos_turisticos_angola.csv` — Conjunto de dados base com destinos turísticos em Angola.
- `modelo_tella.joblib` — Modelo treinado serializado (Joblib) para inferência.

## Como usar
- Notebook: abra `Group09 Final Project.ipynb` e execute as células na ordem.
- Inferência rápida em Python:

```python
from joblib import load
import pandas as pd

model = load("modelo_tella.joblib")
# Exemplo: ler dados e prever (ajuste as colunas conforme o notebook)
df = pd.read_csv("destinos_turisticos_angola.csv")
# X = df[<colunas_de_entrada>]
# preds = model.predict(X)
```

## Dependências
- Python 3.10+
- pandas, scikit-learn, xgboost, seaborn, matplotlib, missingno, autoviz, joblib
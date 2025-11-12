from pathlib import Path
from django.conf import settings
import pandas as pd

_model = None

# Valores padrão baseados no CSV destinos_turisticos_angola.csv
DEFAULTS_BY_CATEGORY = {
    'praia': {
        'preco_transporte_medio': 77658,
        'preco_hospedagem_medio': 107983,
        'preco_alimentacao_medio': 50636,
        'preco_lazer_medio': 64337,
        'indice_sazonalidade': 1.03,
        'pontuacao_popularidade': 79.6,
        'fator_sustentabilidade': 64.9,
    },
    'eco-turismo': {
        'preco_transporte_medio': 67314,
        'preco_hospedagem_medio': 156867,
        'preco_alimentacao_medio': 59697,
        'preco_lazer_medio': 60736,
        'indice_sazonalidade': 1.16,
        'pontuacao_popularidade': 83.3,
        'fator_sustentabilidade': 78.0,
    },
    'cidade': {
        'preco_transporte_medio': 66432,
        'preco_hospedagem_medio': 124270,
        'preco_alimentacao_medio': 50584,
        'preco_lazer_medio': 61539,
        'indice_sazonalidade': 1.12,
        'pontuacao_popularidade': 77.0,
        'fator_sustentabilidade': 69.2,
    },
    'cultural': {
        'preco_transporte_medio': 92873,
        'preco_hospedagem_medio': 135713,
        'preco_alimentacao_medio': 59853,
        'preco_lazer_medio': 56342,
        'indice_sazonalidade': 1.17,
        'pontuacao_popularidade': 83.2,
        'fator_sustentabilidade': 76.2,
    },
    'montanha': {
        'preco_transporte_medio': 81782,
        'preco_hospedagem_medio': 114754,
        'preco_alimentacao_medio': 49809,
        'preco_lazer_medio': 69649,
        'indice_sazonalidade': 1.12,
        'pontuacao_popularidade': 83.0,
        'fator_sustentabilidade': 74.4,
    },
    'histórico': {
        'preco_transporte_medio': 76693,
        'preco_hospedagem_medio': 123290,
        'preco_alimentacao_medio': 45161,
        'preco_lazer_medio': 39853,
        'indice_sazonalidade': 1.07,
        'pontuacao_popularidade': 86.7,
        'fator_sustentabilidade': 60.6,
    },
    'parque': {
        'preco_transporte_medio': 104351,
        'preco_hospedagem_medio': 125482,
        'preco_alimentacao_medio': 51277,
        'preco_lazer_medio': 51305,
        'indice_sazonalidade': 1.10,
        'pontuacao_popularidade': 82.9,
        'fator_sustentabilidade': 61.2,
    }
}

# Mapeamento de tipos Google Places para categorias do modelo
GOOGLE_TYPES_TO_CATEGORY = {
    'tourist_attraction': 'cultural',
    'natural_feature': 'eco-turismo',
    'park': 'parque',
    'beach': 'praia',
    'mountain': 'montanha',
    'museum': 'histórico',
    'church': 'histórico',
    'restaurant': 'cidade',
    'lodging': 'cidade',
    'shopping_mall': 'cidade',
    'locality': 'cidade',
    'administrative_area_level_1': 'cidade',
}

def _model_path():
    """Localiza o novo modelo Tella."""
    base = Path(settings.BASE_DIR)
    # Tenta primeiro na raiz do projeto Django
    fallback1 = base / 'modelo_tella.joblib'
    if fallback1.exists():
        return fallback1
    # Depois na raiz do workspace
    fallback2 = base.parent / 'modelo_tella.joblib'
    return fallback2

def get_model():
    global _model
    if _model is None:
        try:
            from joblib import load
            path = _model_path()
            print(f"[ML] Carregando modelo Tella de: {path}")
            _model = load(path)
            print("[ML] Modelo Tella carregado com sucesso.")
        except Exception as e:
            print(f"[ML] Falha ao carregar modelo Tella: {e}")
            _model = None
    return _model

def map_google_type_to_category(google_types):
    """Mapeia tipos do Google Places para categoria_destino."""
    if not google_types:
        return 'cidade'
    
    for gtype in google_types:
        if gtype in GOOGLE_TYPES_TO_CATEGORY:
            return GOOGLE_TYPES_TO_CATEGORY[gtype]
    
    return 'cidade'  # Padrão

def get_smart_defaults(categoria_destino, rating=None):
    """Retorna valores padrão inteligentes baseados no CSV de Angola."""
    defaults = DEFAULTS_BY_CATEGORY.get(categoria_destino, DEFAULTS_BY_CATEGORY['cidade'])
    
    # Inferir sentimento baseado no rating
    sentimento = 'neutro'
    if rating:
        if rating >= 4.5:
            sentimento = 'positivo'
        elif rating <= 3.0:
            sentimento = 'negativo'
    
    return {
        'tipo_viajante': 'família',  # Mais comum
        'sentimento_avaliacao': sentimento,
        **defaults
    }

def estimate_cost(features: dict):
    """Estima custo usando o novo modelo Tella."""
    model = get_model()
    if model is None:
        print("[ML] Modelo Tella indisponível.")
        return None
    
    df = pd.DataFrame([features])
    print(f"[ML] Tella predict -> {df.iloc[0].to_dict()}")
    
    try:
        pred = model.predict(df)
        print(f"[ML] Tella pred: {pred}")
        return float(pred[0])
    except Exception as e:
        print(f"[ML] Erro Tella: {e}")
        return None

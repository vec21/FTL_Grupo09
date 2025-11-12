from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
import requests
import math
from urllib.parse import quote
from django.core.cache import cache
from .forms import UserRegistrationForm, LoginForm
from .models import Trip
from .ml import get_model, estimate_cost


def home(request):
    return render(request, 'core/home.html')

@login_required(login_url='/login/')
def destinos(request):
    return render(request, 'core/destinos.html')

@login_required(login_url='/login/')
def planejador(request):
    # Recupera última estimativa e lugar, se existir
    # Recupera última estimativa e lugar, se existir
    est = request.session.get('last_estimate')
    place = request.session.get('last_place')
    return render(request, 'core/planejador.html', {"estimate": est, "place": place})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            messages.success(request, f"Bem-vindo(a), {user.first_name or user.username}!")
            return redirect('core:home')
        else:
            messages.error(request, 'Credenciais inválidas. Tente novamente.')
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})

def cadastro(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, 'Conta criada com sucesso!')
            return redirect('core:home')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = UserRegistrationForm()
    return render(request, 'core/cadastro.html', {'form': form})

def logout_view(request):
    auth_logout(request)
    messages.success(request, 'Sessão terminada com sucesso.')
    return redirect('core:home')

def ui_placeholder(request):
    return render(request, 'core/ui.html')

def sobre(request):
    return render(request, 'core/sobre.html')

def contato(request):
    return render(request, 'core/contato.html')


# Helpers de busca/feature engineering
def _infer_subcategoria(types):
    if not types:
        return None
    mapping = {
        "museum": "Museu",
        "restaurant": "Restaurante",
        "bar": "Bar",
        "cafe": "Café",
        "park": "Parque",
        "tourist_attraction": "Atração Turística",
        "art_gallery": "Galeria de Arte",
        "night_club": "Clube Noturno",
        "lodging": "Hospedagem",
        "hotel": "Hotel",
    }
    for t in types:
        if t in mapping:
            return mapping[t]
    return types[0]


def _photo_url_from_photos(host: str, place_id: str, photos):
    try:
        if not photos:
            return None
        name = photos[0].get('name') or photos[0].get('photo_reference')
        photo_ref = None
        if isinstance(name, str):
            if 'photos/' in name:
                photo_ref = name.split('photos/')[-1]
            else:
                photo_ref = name
        if not photo_ref:
            return None
        # Usa proxy local para tratar headers e redirecionamento
        return reverse('core:api_place_photo', args=[place_id, photo_ref])
    except Exception:
        return None


def _haversine_km(lat: float, lng: float, center_lat: float = -8.8383, center_lng: float = 13.2344):
    try:
        R = 6371.0
        dlat = math.radians(lat - center_lat)
        dlng = math.radians(lng - center_lng)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(center_lat)) * math.cos(math.radians(lat)) * math.sin(dlng / 2) ** 2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    except Exception:
        return None


# API: Busca de lugares (RapidAPI Google Places New V2)
@login_required(login_url='/login/')
def api_places_search(request):
    query = request.GET.get('q')
    if not query:
        return JsonResponse({'results': []})
    # Cache key e TTL (sanitizado para compat. memcached)
    q_norm = ' '.join(query.strip().lower().split())
    cache_key = f"places:{quote(q_norm, safe=':+')}"
    cached = cache.get(cache_key)
    if cached is not None:
        return JsonResponse({'results': cached})
    # Validação de chave
    if not getattr(settings, 'RAPIDAPI_KEY', None):
        return JsonResponse({'error': 'RAPIDAPI_KEY não configurada no servidor.', 'results': []}, status=500)
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.userRatingCount,places.types,places.photos',
        'x-rapidapi-host': settings.RAPIDAPI_HOST,
        'x-rapidapi-key': settings.RAPIDAPI_KEY or ''
    }
    body_base = {
        "maxResultCount": 6,
        "openNow": False,
        "strictTypeFiltering": False,
        "languageCode": "pt",
        "regionCode": "AO",
        "locationBias": {
            "circle": {
                "center": {"latitude": -8.8383, "longitude": 13.2344},
                "radius": 30000.0
            }
        },
    }
    def _do_search(q: str):
        body = dict(body_base)
        body["textQuery"] = q
        resp = requests.post(f"https://{settings.RAPIDAPI_HOST}/v1/places:searchText", json=body, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.json()
    try:
        data = _do_search(query)
        places = data.get('places', []) or []
        if not places and 'luanda' not in query.strip().lower():
            data = _do_search(query + ' Luanda')
            places = data.get('places', []) or []
        items = []
        for p in places[:6]:
            raw_id = p.get('id') or p.get('name') or ''
            place_id = raw_id.split('/')[-1] if isinstance(raw_id, str) else ''
            types = p.get('types') or []
            categoria_principal = types[0] if types else None
            subcategoria = _infer_subcategoria(types) if types else None
            photo_url = None
            try:
                photo_url = request.build_absolute_uri(
                    _photo_url_from_photos(settings.RAPIDAPI_HOST, place_id, p.get('photos'))
                )
            except Exception:
                photo_url = None
            items.append({
                'name': p.get('displayName', {}).get('text'),
                'address': p.get('formattedAddress'),
                'lat': p.get('location', {}).get('latitude'),
                'lng': p.get('location', {}).get('longitude'),
                'rating': p.get('rating'),
                'userRatingCount': p.get('userRatingCount'),
                'categoria_principal': categoria_principal,
                'subcategoria': subcategoria,
                'provincia': 'Luanda',
                'photo_url': photo_url,
                'id': place_id,
            })
        # guarda no cache
        cache.set(cache_key, items, timeout=getattr(settings, 'PLACES_CACHE_TTL', 600))
        return JsonResponse({'results': items})
    except Exception as e:
        return JsonResponse({'error': str(e), 'results': []}, status=500)


# Proxy de foto: redireciona para URL pública da imagem
@login_required(login_url='/login/')
def api_place_photo(request, place_id: str, photo_ref: str):
    if not getattr(settings, 'RAPIDAPI_KEY', None):
        return JsonResponse({'error': 'RAPIDAPI_KEY não configurada no servidor.'}, status=500)
    try:
        # Tenta primeiro obter JSON com skipHttpRedirect=true para extrair photoUri
        base = f"https://{settings.RAPIDAPI_HOST}/v1/places/{place_id}/photos/{photo_ref}/media"
        url_json = base + "?maxWidthPx=800&maxHeightPx=800&skipHttpRedirect=true"
        headers = {
            'x-rapidapi-host': settings.RAPIDAPI_HOST,
            'x-rapidapi-key': settings.RAPIDAPI_KEY or ''
        }
        # Primeiro modo JSON
        resp_json = requests.get(url_json, headers=headers, timeout=20)
        if resp_json.status_code == 200:
            try:
                data = resp_json.json()
                photo_uri = data.get('photoUri') or data.get('photo_uri')
                if photo_uri:
                    return HttpResponseRedirect(photo_uri)
            except Exception:
                pass
        # Segundo modo: sem skipHttpRedirect para pegar Location
        url_redirect = base + "?maxWidthPx=800&maxHeightPx=800"
        resp = requests.get(url_redirect, headers=headers, timeout=20, allow_redirects=False)
        if resp.status_code in (301, 302, 303, 307, 308):
            loc = resp.headers.get('Location') or resp.headers.get('location')
            if loc:
                return HttpResponseRedirect(loc)
        # Último fallback: baixar conteúdo direto (pode ser imagem ou erro)
        resp_final = requests.get(url_redirect, headers=headers, timeout=20)
        content_type = resp_final.headers.get('Content-Type', 'image/jpeg')
        from django.http import HttpResponse
        return HttpResponse(resp_final.content, content_type=content_type)
    except Exception as e:
        return JsonResponse({'error': f'foto_indisponivel: {e}'}, status=500)


# POST: Estimar custo para um lugar selecionado e redirecionar ao planejador
@login_required(login_url='/login/')
def estimate_place_cost(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método inválido'}, status=405)
    
    # Dados básicos da API/formulário
    name = request.POST.get('name')
    address = request.POST.get('address')
    lat = request.POST.get('lat')
    lng = request.POST.get('lng')
    rating = request.POST.get('rating') or '0'
    reviews = request.POST.get('userRatingCount') or '0'
    categoria_principal = request.POST.get('categoria_principal') or 'place'
    
    # Inputs do usuário para personalização
    tipo_viajante = request.POST.get('tipo_viajante') or 'família'
    duracao_dias = request.POST.get('duracao_dias') or '3'
    nivel_orcamento = request.POST.get('nivel_orcamento') or 'medio'
    precisa_transporte = request.POST.get('precisa_transporte') or 'sim'
    precisa_hospedagem = request.POST.get('precisa_hospedagem') or 'sim'
    
    # Converter coordenadas
    try:
        lat_f = float(lat) if lat else 0.0
        lng_f = float(lng) if lng else 0.0
        rating_f = float(rating)
        reviews_f = float(reviews)
        duracao_f = float(duracao_dias)
    except Exception:
        lat_f = lng_f = rating_f = reviews_f = duracao_f = 0.0
    
    # Mapear categoria do Google Places para categoria do modelo
    from .ml import map_google_type_to_category, get_smart_defaults
    
    # Se categoria_principal é um tipo do Google, mapear
    if categoria_principal in ['tourist_attraction', 'natural_feature', 'park', 'beach', 'mountain', 'museum', 'church', 'restaurant', 'lodging', 'shopping_mall', 'locality']:
        categoria_destino = map_google_type_to_category([categoria_principal])
    else:
        # Mapear valores do formulário para categorias do modelo
        category_map = {
            'place': 'cidade',
            'restaurant': 'cidade', 
            'hotel': 'cidade',
            'attraction': 'cultural',
            'shopping': 'cidade'
        }
        categoria_destino = category_map.get(categoria_principal, 'cidade')
    
    # Obter valores padrão inteligentes baseados no CSV
    defaults = get_smart_defaults(categoria_destino, rating_f)
    
    # Ajustar valores baseados no nível de orçamento
    multiplicador_orcamento = {
        'economico': 0.7,
        'medio': 1.0,
        'luxo': 1.5
    }.get(nivel_orcamento, 1.0)
    
    # Aplicar multiplicador aos preços
    preco_transporte = defaults['preco_transporte_medio'] * multiplicador_orcamento
    preco_hospedagem = defaults['preco_hospedagem_medio'] * multiplicador_orcamento
    preco_alimentacao = defaults['preco_alimentacao_medio'] * multiplicador_orcamento
    preco_lazer = defaults['preco_lazer_medio'] * multiplicador_orcamento
    
    # Zerar custos se usuário não precisa
    if precisa_transporte == 'nao':
        preco_transporte = 0.0
    if precisa_hospedagem == 'nao':
        preco_hospedagem = 0.0
    
    # Montar features para o novo modelo
    features = {
        'categoria_destino': categoria_destino,
        'classificacao_media': rating_f,
        'num_avaliacoes': int(reviews_f),
        'sentimento_avaliacao': defaults['sentimento_avaliacao'],
        'tipo_viajante': tipo_viajante,
        'preco_transporte_medio': preco_transporte,
        'preco_hospedagem_medio': preco_hospedagem,
        'preco_alimentacao_medio': preco_alimentacao,
        'preco_lazer_medio': preco_lazer,
        'indice_sazonalidade': defaults['indice_sazonalidade'],
        'pontuacao_popularidade': defaults['pontuacao_popularidade'],
        'fator_sustentabilidade': defaults['fator_sustentabilidade'],
        'latitude': lat_f,
        'longitude': lng_f,
    }
    
    cost = estimate_cost(features)
    
    # Multiplicar pelo número de dias
    if cost and duracao_f > 0:
        cost = cost * duracao_f
    
    request.session['last_estimate'] = cost
    
    if cost is None:
        request.session['last_estimate_error'] = 'Falha ao calcular estimativa com modelo Tella.'
    else:
        request.session.pop('last_estimate_error', None)
    
    # Salvar dados do lugar na sessão
    request.session['last_place'] = {
        'name': name,
        'address': address,
        'lat': lat,
        'lng': lng,
        'rating': rating,
        'userRatingCount': reviews,
        'categoria_destino': categoria_destino,
        'tipo_viajante': tipo_viajante,
        'duracao_dias': duracao_dias,
        'nivel_orcamento': nivel_orcamento,
        'precisa_transporte': precisa_transporte,
        'precisa_hospedagem': precisa_hospedagem,
    }
    
    return redirect('core:planejador')

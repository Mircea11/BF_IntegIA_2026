"""B.5 product adviser: real catalog, stable Qdrant ids, live stock, PostgreSQL memory.
No writes to GitHub, Gmail or public services except read-only DummyJSON GET.
"""
import json, logging, os, re, time
from datetime import datetime, timezone
from typing import Optional

import psycopg
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(levelname)s %(message)s')
log = logging.getLogger('b5')

CATALOG_URL = 'https://dummyjson.com/products?limit=0&select=id,title,description,category,price,brand'
DUMMY = os.getenv('DUMMYJSON_URL', 'https://dummyjson.com').rstrip('/')
QDRANT = os.getenv('QDRANT_URL', 'http://127.0.0.1:6333').rstrip('/')
EMBED = os.getenv('EMBED_URL', 'http://172.21.0.1:8001/v1').rstrip('/')
LLM = os.getenv('LLM_URL', 'http://172.21.0.1:8000/v1').rstrip('/')
EMBED_MODEL = os.getenv('EMBED_MODEL', 'bge-m3')
LLM_MODEL = os.getenv('LLM_MODEL', 'veltis-llm')
PG_DSN = os.getenv('PG_DSN', 'postgresql://b5user:b5pass@127.0.0.1:5433/b5shop')
COLLECTION = 'b5_shop_products_v1'
TIMEOUT = 30

app = FastAPI(title='B.5 Conseiller Produit - local Z4')
http = requests.Session()

class ChatIn(BaseModel):
    session_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=2000)


def req(method, url, **kwargs):
    kwargs.setdefault('timeout', TIMEOUT)
    r = http.request(method, url, **kwargs)
    r.raise_for_status()
    return r.json()


def db():
    return psycopg.connect(PG_DSN, connect_timeout=8)


def init_db():
    with db() as conn:
        with conn.cursor() as cur:
            cur.execute('''CREATE TABLE IF NOT EXISTS b5_messages (
                id BIGSERIAL PRIMARY KEY,
                session_id VARCHAR(128) NOT NULL,
                role VARCHAR(16) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW())''')
            cur.execute('''CREATE TABLE IF NOT EXISTS b5_profile (
                session_id VARCHAR(128) PRIMARY KEY,
                name TEXT NOT NULL)''')
            cur.execute('CREATE INDEX IF NOT EXISTS b5_messages_session ON b5_messages(session_id,id)')


def remember(session, role, content):
    with db() as conn:
        conn.execute('INSERT INTO b5_messages(session_id,role,content) VALUES (%s,%s,%s)',
                     (session, role, content))


def recent(session):
    with db() as conn:
        rows = conn.execute('''SELECT role,content FROM b5_messages
            WHERE session_id=%s ORDER BY id DESC LIMIT 8''', (session,)).fetchall()
    return list(reversed(rows))


def name_get(session):
    with db() as conn:
        row = conn.execute('SELECT name FROM b5_profile WHERE session_id=%s', (session,)).fetchone()
    return row[0] if row else None


def name_put(session, name):
    with db() as conn:
        conn.execute('''INSERT INTO b5_profile(session_id,name) VALUES (%s,%s)
            ON CONFLICT(session_id) DO UPDATE SET name=EXCLUDED.name''', (session,name))


def embedding_batch(texts):
    result = req('POST', EMBED+'/embeddings',
                 json={'model': EMBED_MODEL, 'input': texts}, timeout=180)
    rows = sorted(result['data'], key=lambda x: x['index'])
    vectors = [row['embedding'] for row in rows]
    if len(vectors) != len(texts) or not vectors or not vectors[0]:
        raise RuntimeError('Réponse embeddings incomplète')
    return vectors


def qcount():
    return req('POST', QDRANT+'/collections/'+COLLECTION+'/points/count',
               json={'exact':True})['result']['count']


def qpoints():
    points = []
    offset = None
    while True:
        payload = {'limit':256, 'with_payload':True, 'with_vector':False}
        if offset is not None:
            payload['offset'] = offset
        page = req('POST', QDRANT+'/collections/'+COLLECTION+'/points/scroll',json=payload)
        points += page['result']['points']
        offset = page['result'].get('next_page_offset')
        if offset is None:
            break
    return points


def ensure_collection(vector_size):
    url = QDRANT+'/collections/'+COLLECTION
    info = http.get(url,timeout=15)
    if info.status_code == 404:
        req('PUT',url,json={'vectors':{'size':vector_size,'distance':'Cosine'}})
        return
    info.raise_for_status()
    actual = info.json()['result']['config']['params']['vectors']['size']
    if actual != vector_size:
        raise RuntimeError(f'Collection vector size {actual} != embedder {vector_size}; model/config mismatch')


def fetch_catalog():
    # Explicit id in select prevents join failures. DummyJSON may change catalogue size.
    data = req('GET', DUMMY+'/products',params={
        'limit':0, 'select':'id,title,description,category,price,brand'}, timeout=40)
    products = data.get('products',[])
    if not products or not all(isinstance(p.get('id'),int) for p in products):
        raise RuntimeError('Catalogue vide ou identifiants manquants')
    ids = [p['id'] for p in products]
    if len(ids) != len(set(ids)):
        raise RuntimeError('IDs doublonnés dans DummyJSON')
    return products


def product_text(p):
    return ('Produit : '+str(p['title'])+'\n'+
            'Marque : '+str(p.get('brand') or '')+'\n'+
            'Catégorie : '+str(p.get('category') or '')+'\n'+
            'Description : '+str(p.get('description') or ''))


@app.post('/reindex')
def reindex():
    try:
        products = fetch_catalog()
        # Fast, stable IDs; second run overwrites, never appends duplicates.
        for start in range(0,len(products),12):
            batch = products[start:start+12]
            vectors = embedding_batch([product_text(p) for p in batch])
            ensure_collection(len(vectors[0]))
            points = [{'id':p['id'],'vector':v,'payload':{
                'id':p['id'],'title':p['title'],'description':p.get('description') or '',
                'category':p.get('category') or '', 'price':p['price'],
                'brand':p.get('brand') or ''}} for p,v in zip(batch,vectors)]
            req('PUT',QDRANT+'/collections/'+COLLECTION+'/points',
                params={'wait':'true'},json={'points':points},timeout=120)
        existing_ids = {p['id'] for p in qpoints()}
        current_ids = {p['id'] for p in products}
        obsolete = list(existing_ids-current_ids)
        if obsolete:
            req('POST',QDRANT+'/collections/'+COLLECTION+'/points/delete',
                params={'wait':'true'},json={'points':obsolete},timeout=120)
        count = qcount()
        if count != len(products):
            raise RuntimeError(f'Index incomplet: attendu {len(products)}, obtenu {count}')
        return {'ok':True,'source_count':len(products),'qdrant_count':count,
                'removed_old_points':len(obsolete),'matches_exercise_194': count==194}
    except Exception as e:
        log.exception('Reindex failed')
        raise HTTPException(status_code=502,detail=str(e))


def stock_now(pid):
    try:
        p = req('GET',DUMMY+f'/products/{pid}',
                params={'select':'id,title,price,stock,availabilityStatus'},timeout=15)
        # Must check both stock and availabilityStatus, not silently assume.
        if not isinstance(p.get('stock'),int) or p.get('price') is None:
            raise ValueError('Stock/prix absent')
        return p
    except Exception as e:
        log.warning('Stock unavailable for %s: %s',pid,e)
        return None


def tokenize(text):
    return {x for x in re.findall(r'[a-zà-ÿ0-9]{3,}',text.lower())
            if x not in {'une','pour','avec','quel','quelle','voudrais','cherche','moins',
                         'dans','des','les','est','qui','aux','sur','je','mon','plus','euros'}}


def classify(query, history):
    """Nemotron supplies search reformulation; data/output checked independently."""
    fallback = {'intent':'products','search_query':query}
    try:
        messages = [ {'role':'system','content':(
          'Réponds UNIQUEMENT en JSON compact avec exactement les clés '
          '"intent" ("products" ou "outside") et "search_query" (texte). '
          'Tu es dans une boutique. Si la demande concerne autre chose que '
          'les produits vendus (restaurant, météo, politique, voyage), intent="outside". '
          'Pour produits, enrichis la recherche avec synonymes (volley=volleyball, '
          'smartphone=téléphone, pâtes=pasta/cookware) et tiens compte du contexte. '
          'Ne fabrique pas de produit, de prix, ni de stock.')},
          {'role':'user','content':'Contexte récent: '+json.dumps(history[-4:],ensure_ascii=False)+
           '\nNouvelle demande: '+query}]
        result=req('POST',LLM+'/chat/completions',json={
            'model':LLM_MODEL,'messages':messages,'temperature':0,
            'max_tokens':150,'chat_template_kwargs':{'enable_thinking':False}},timeout=100)
        txt=(result['choices'][0]['message'].get('content') or '').strip()
        match=re.search(r'\{.*?\}',txt,re.S)
        if match:
            obj=json.loads(match.group(0))
            if (obj.get('intent') in ('outside','products') and isinstance(obj.get('search_query'),str)
                and obj['search_query'].strip()):
                return obj
    except Exception as e:
        log.warning('LLM reformulation unavailable: %s',e)
    return fallback


def outside_rule(text):
    return bool(re.search(r'\b(restaurant|restaurants|resto|météo|prévisions météo|président|capitale de|élection|politique|hôtel|hotel|napoléon|géographie|histoire de belgique)\b',text.lower()))


def rank_candidates(query, search_query):
    # Deterministic bilingual synonyms avoid relying exclusively on Nemotron.
    qlower = query.lower()
    extra = []
    if 'volley' in qlower: extra += ['volleyball', 'sports accessories', 'ball']
    if 'tennis' in qlower: extra += ['tennis racket', 'sports accessories']
    if 'pât' in qlower or 'pasta' in qlower: extra += ['pasta', 'cookware', 'kitchen']
    if 'smartphone' in qlower or 'téléphone' in qlower: extra += ['smartphone', 'mobile phone']
    enriched = search_query + ' ' + ' '.join(extra)
    vector = embedding_batch([enriched])[0]
    hits=req('POST',QDRANT+'/collections/'+COLLECTION+'/points/query',json={
        'query':vector,'limit':60,'with_payload':True})['result']['points']
    all_points = qpoints()
    scored = {int(p['id']):(float(p['score']),p['payload']) for p in hits}
    words = tokenize(query+' '+enriched)
    words |= set([x for x in ('volleyball','tennis','smartphone','samsung','pasta')
                  if x in enriched.lower()])
    # Include explicit matching items even if vector top-k missed them.
    for p in all_points:
        pid=int(p['id'])
        desc=(p['payload'].get('title','')+' '+p['payload'].get('brand','')+' '+
              p['payload'].get('category','')).lower()
        if words.intersection(tokenize(desc)) and pid not in scored:
            scored[pid]=(0.0,p['payload'])
    ranked=[]
    for pid,(similarity,p) in scored.items():
        title=tokenize(p['title']); all_words=tokenize(product_text(p))
        boost=0.22*len(words & title)+0.035*len(words & all_words)
        ranked.append((similarity+boost,similarity,p))
    ranked.sort(key=lambda r:r[0],reverse=True)
    return ranked


def budget_from(query):
    match=re.search(r'(?:moins de|sous|inférieur à|maximum|max|budget(?: de)?)\s*(\d+(?:[.,]\d+)?)\s*(?:€|euros?)?',query.lower())
    return float(match.group(1).replace(',','.')) if match else None


def shop_answer(query, search_query):
    ranked=rank_candidates(query,search_query)
    if not ranked:
        return 'Je ne trouve pas de produit correspondant dans notre catalogue.',[],0
    budget=budget_from(query)
    allbrands={str(p['payload'].get('brand') or '').lower():str(p['payload'].get('brand'))
               for p in qpoints() if p['payload'].get('brand')}
    brand = next((v for k,v in allbrands.items() if k in query.lower()),None)
    # Consider all the top candidate matches; validate stock using live GET by id.
    candidates=[]; unavailable=[]
    for weighted,similarity,p in ranked[:35]:
        # Avoid vague low-relevance hits.
        if weighted < 0.24: continue
        live=stock_now(p['id'])
        if live is None: continue  # Unknown stock is never treated as available
        if live.get('id') is not None and int(live['id']) != int(p['id']):
            continue  # A different product is not a valid stock check.
        if live.get('title') != p['title']:
            continue  # Catalog changed: refuse unverified product identity
        item={'id':p['id'],'title':live['title'],'brand':p.get('brand',''),
              'category':p.get('category',''),'price':live['price'],
              'stock':live['stock'],'availability':live.get('availabilityStatus',''),
              'score':weighted}
        relevant_budget=budget is None or float(live['price']) < budget
        avail=(live['stock']>0 and str(live.get('availabilityStatus','')).strip().lower() not in ('out of stock','rupture de stock','discontinued','unavailable'))
        if not avail:
            unavailable.append(item)
        if avail and relevant_budget:
            candidates.append(item)
    # Strongly prefer requested brand, but offer other brands as explicit alternatives.
    preferred=[p for p in candidates if not brand or p['brand'].lower()==brand.lower()]
    # Identify requested out-of-stock item using both French and English keywords.
    qwords=tokenize(query)
    if 'volley' in query.lower(): qwords.add('volleyball')
    bad=next((p for p in unavailable if qwords & tokenize(p['title'])),None)
    # Alternatives from the same category are preferable after a stock-out.
    pool=preferred or candidates
    if bad:
        pool=sorted(pool, key=lambda p: (p['category'] != bad['category'], -p['score']))
    chosen=pool[:3]
    if not chosen:
        if bad:
            return f"{bad['title']} est en rupture de stock. Je ne trouve pas d’alternative disponible répondant à vos critères dans le catalogue.",[],len(unavailable)
        return 'Je ne trouve pas de produit disponible correspondant à vos critères dans notre catalogue.',[],len(unavailable)
    lines=[]
    if bad and any(x['id']!=bad['id'] for x in chosen):
        lines.append(f"{bad['title']} est en rupture de stock. Voici une alternative en stock :")
    else:
        lines.append('Voici les produits du catalogue disponibles :')
    if brand and not preferred:
        lines.append(f"Aucun produit {brand} disponible ne correspond à tous vos critères ; alternatives d’autres marques :")
    for x in chosen:
        price=f"{float(x['price']):.2f}".replace('.',',')
        lines.append(f"- {x['title']} — prix catalogue : {price} (stock : {x['stock']})")
    return '\n'.join(lines),chosen,len(unavailable)


@app.get('/health')
def health():
    checks={}
    for k,url in [('qdrant',QDRANT+'/healthz'),('embedding',EMBED+'/models'),('nemotron',LLM+'/models')]:
        try: checks[k]=http.get(url,timeout=4).status_code==200
        except Exception: checks[k]=False
    try:
        with db() as conn:conn.execute('SELECT 1')
        checks['postgres']=True
    except Exception: checks['postgres']=False
    return {'services':checks,'ready':all(checks.values())}


@app.post('/chat')
def chat(data:ChatIn):
    try:
        init_db()
        session,query = data.session_id,data.message.strip()
        prev=recent(session)
        match=re.search(r"\bje m['’]appelle\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ'-]{1,40})",query,re.I)
        if match:
            name=match.group(1).strip(".-!?,;: ")
            name_put(session,name)
            reply=f'Enchanté {name}. Je retiendrai votre prénom pour cette conversation.'
            items=[]
        elif re.search(r'\b(comment|quel|c’est quoi)\b.*\b(m\s*[\'’]?appelle|mon prénom|mon nom)\b',query.lower()):
            name=name_get(session)
            reply=(f'Vous vous appelez {name}.' if name else
                   'Je ne connais pas encore votre prénom dans cette conversation.')
            items=[]
        elif outside_rule(query):
            reply='Je ne peux répondre qu’aux questions concernant les produits de notre catalogue.'
            items=[]
        else:
            classified=classify(query,prev)
            if classified['intent']=='outside':
                reply='Je ne peux répondre qu’aux questions concernant les produits de notre catalogue.'
                items=[]
            else:
                reply,items,_=shop_answer(query,classified['search_query'])
        remember(session,'user',query)
        remember(session,'assistant',reply)
        return {'session_id':session,'answer':reply,'products':items}
    except requests.HTTPError as e:
        log.exception('Upstream failure')
        raise HTTPException(status_code=502,detail=f'Service externe indisponible: {e.response.status_code if e.response else "HTTP"}')
    except Exception as e:
        log.exception('Chat failure')
        raise HTTPException(status_code=503,detail='Service ou données indisponibles; aucun produit non vérifié ne sera recommandé.')

"""Offline integration-style tests: mocked vendor endpoints and persistent session store."""
import sys, types, importlib.util, unittest
# Installing application dependencies is not required for this offline test harness.
if 'psycopg' not in sys.modules:
    sys.modules['psycopg']=types.ModuleType('psycopg')
spec=importlib.util.spec_from_file_location('b5_app','app.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class B5Tests(unittest.TestCase):
    def setUp(self):
        self.products=[]
        known={
          1:('Samsung Galaxy S8','Samsung','smartphones',390,0),
          2:('Samsung Galaxy A54','Samsung','smartphones',349,7),
          3:('Volleyball','', 'sports-accessories',18,0),
          4:('Basketball','', 'sports-accessories',22,5),
          5:('Tennis Racket','', 'sports-accessories',65,9),
          6:('Pasta Cooking Pot','', 'kitchen-accessories',45,12),
          7:('Budget Smartphone','Moto', 'smartphones',220,5),
        }
        for idx in range(1,195):
            title,brand,cat,price,stock=known.get(idx,(f'Filler product {idx}', '', 'misc', 900, 1))
            self.products.append({'id':idx,'title':title,'brand':brand,'category':cat,'description':title+' suitable for use', 'price':price,'stock':stock,'availabilityStatus':'In Stock' if stock else 'Out of Stock'})
        self.points={}
        self.names={};self.messages={}
        self._orig={k:getattr(mod,k) for k in ('req','init_db','remember','recent','name_get','name_put','embedding_batch','classify')}
        mod.req=self.fake_req
        mod.init_db=lambda:None
        mod.remember=lambda s,r,c:self.messages.setdefault(s,[]).append((r,c))
        mod.recent=lambda s:self.messages.get(s, [])[-8:]
        mod.name_get=lambda s:self.names.get(s)
        mod.name_put=lambda s,n:self.names.__setitem__(s,n)
        mod.embedding_batch=lambda inp:[[1.,0.,0.] for i in inp]
        mod.classify=lambda query,hist:{'intent':'products','search_query':query+' '+'volleyball' if 'volley' in query else query}
    def tearDown(self):
        for k,v in self._orig.items():setattr(mod,k,v)
    def fake_req(self,method,url,**kwargs):
        if '/products' in url:
            if url.endswith('/products'):
                return {'products':[{k:v for k,v in p.items() if k not in ('stock','availabilityStatus')} for p in self.products]}
            pid=int(url.rsplit('/',1)[1]);return self.products[pid-1]
        if url.endswith('/points/count'):
            return {'result':{'count':len(self.points)}}
        if url.endswith('/points/scroll'):
            payload=kwargs.get('json',{});offset=payload.get('offset')
            points=[{'id':p['id'],'payload':p['payload']} for p in sorted(self.points.values(),key=lambda r:r['id'])]
            start=next((i for i,p in enumerate(points) if p['id']>=offset),len(points)) if offset is not None else 0
            limit=payload.get('limit',256);items=points[start:start+limit]
            return {'result':{'points':items,'next_page_offset':points[start+limit]['id'] if start+limit<len(points) else None}}
        if url.endswith('/points') and method=='PUT':
            for p in kwargs['json']['points']:self.points[p['id']]=p
            return {'status':'ok'}
        if url.endswith('/points/delete'):
            for id_ in kwargs['json']['points']:self.points.pop(id_,None)
            return {'status':'ok'}
        if url.endswith('/points/query'):
            return {'result':{'points':[{'id':p['id'],'score':0.35,'payload':p['payload']} for p in list(self.points.values())[:60]]}}
        raise AssertionError(f'Unexpected mock API call: {method} {url}')
    def bootstrap(self):
        orig=mod.ensure_collection
        try:
            mod.ensure_collection=lambda _:None
            return mod.reindex()
        finally:mod.ensure_collection=orig
    def test_01_reindex_twice_no_duplicates_and_delete_obsolete(self):
        self.assertEqual(self.bootstrap()['qdrant_count'],194)
        self.assertEqual(self.bootstrap()['qdrant_count'],194)
        self.products=self.products[:190]
        self.assertEqual(self.bootstrap()['qdrant_count'],190)
    def test_02_samsung_never_sell_out_of_stock(self):
        self.bootstrap()
        x=mod.chat(mod.ChatIn(session_id='t',message='Je cherche un smartphone Samsung à moins de 500 €'))
        self.assertTrue(any(p['title']=='Samsung Galaxy A54' for p in x['products']))
        self.assertFalse(any(p['title']=='Samsung Galaxy S8' for p in x['products']))
        self.assertIn('prix catalogue : 349,00',x['answer'])
    def test_03_volleyball_break_alternative(self):
        self.bootstrap()
        x=mod.chat(mod.ChatIn(session_id='t',message='Je voudrais un ballon de volley'))
        self.assertNotIn('Volleyball —',x['answer'])
        self.assertTrue(x['products'])
        self.assertTrue(all(p['stock']>0 for p in x['products']))
    def test_04_outside(self):
        x=mod.chat(mod.ChatIn(session_id='t',message='Quel est le meilleur restaurant de Bruxelles ?'))
        self.assertIn('catalogue',x['answer'])
        self.assertEqual(x['products'],[])
    def test_05_name_persists_in_database_state(self):
        a=mod.chat(mod.ChatIn(session_id='session-7',message="Je m'appelle Sam"))
        self.assertIn('Sam',a['answer'])
        # A process restart would reset runtime memory, not PostgreSQL tables.
        b=mod.chat(mod.ChatIn(session_id='session-7',message="Comment je m'appelle ?"))
        self.assertIn('Sam',b['answer'])
    def test_07_budget_and_brand_are_respected(self):
        self.bootstrap()
        x=mod.chat(mod.ChatIn(session_id='t',message='Je cherche un smartphone Samsung à moins de 300 €'))
        self.assertFalse(any(float(p['price'])>=300 for p in x['products']))
        self.assertFalse(any(p['title']=='Samsung Galaxy S8' for p in x['products']))
    def test_09_semantic_use_cases(self):
        self.bootstrap()
        tennis=mod.chat(mod.ChatIn(session_id='tennis',message='Un cadeau pour un joueur de tennis'))
        pasta=mod.chat(mod.ChatIn(session_id='pasta',message='De quoi cuisiner des pâtes'))
        self.assertTrue(tennis['products'])
        self.assertTrue(pasta['products'])
        self.assertTrue(all(p['stock']>0 for p in tennis['products']+pasta['products']))

    def test_08_session_isolation(self):
        mod.chat(mod.ChatIn(session_id='session-A',message="Je m'appelle Sam"))
        b=mod.chat(mod.ChatIn(session_id='session-B',message="Comment je m'appelle ?"))
        self.assertNotIn('Sam',b['answer'])

    def test_06_unknown_live_stock_does_not_get_recommended(self):
        self.bootstrap()
        old=mod.stock_now
        try:
            mod.stock_now=lambda pid: None
            x=mod.chat(mod.ChatIn(session_id='t',message='Je cherche un smartphone Samsung à moins de 500 €'))
            self.assertEqual(x['products'],[])
        finally: mod.stock_now=old

    def test_10_price_does_not_invent_currency(self):
        self.bootstrap()
        x=mod.chat(mod.ChatIn(session_id='t',message='Je cherche un smartphone Samsung à moins de 500 €'))
        self.assertNotIn('349,00 €',x['answer'])
        self.assertIn('prix catalogue : 349,00',x['answer'])

    def test_11_zero_stock_never_recommended(self):
        self.bootstrap()
        for p in self.products:
            p['stock']=0
            p['availabilityStatus']='Out of Stock'
        x=mod.chat(mod.ChatIn(session_id='t',message='Je voudrais un ballon de volley'))
        self.assertEqual(x['products'],[])

if __name__=='__main__': unittest.main(verbosity=2)

"""Unit tests for pure benchmark logic; no Qdrant or model service needed."""
import ast
import json
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path
from statistics import mean

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE/'scripts/benchmark_mmr_e17.py'


def load_pure_functions(*names):
    tree=ast.parse(SCRIPT.read_text(encoding='utf8'))
    selected=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
    namespace={'Path':Path, 'json':json, 'defaultdict':defaultdict, 'mean':mean,
               'ARMS':('rrf5','mmr5','rrf30_rerank5','rrf15_rerank5','mmr15_rerank5')}
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(SCRIPT),'exec'),namespace)
    return namespace

class BenchmarkPureTests(unittest.TestCase):
    def test_python_parse(self):
        ast.parse(SCRIPT.read_text(encoding='utf8'))
    def test_documentation(self):
        self.assertIn('multi_hop',(BASE/'docs/E17_BENCHMARK_README.md').read_text())
    def test_dataset_selection_and_exclusion(self):
        fun=load_pure_functions('select_questions')['select_questions']
        sample=[{'type':'table','id':'Q001'},{'type':'multi_hop','id':'Q002'},
                {'type':'out_of_corpus','id':'Q003'}]
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'eval.json';p.write_text(json.dumps(sample))
            self.assertEqual([x['id'] for x in fun(p,None,['multi_hop'])],['Q002'])
            self.assertEqual([x['id'] for x in fun(p,2,['table','multi_hop'])],['Q001','Q002'])
    def test_summary_calculation(self):
        summarize=load_pure_functions('summary')['summary']
        rows=[{'arm':'rrf5','hit_at_5':1,'fact_recall_at_5':1.0,'ndcg_at_5':1.0,'query_latency_seconds':2,'mean_jaccard':0.2},
              {'arm':'rrf5','hit_at_5':0,'fact_recall_at_5':0.5,'ndcg_at_5':0.0,'query_latency_seconds':4,'mean_jaccard':0.4}]
        result=summarize(rows)['rrf5']
        self.assertAlmostEqual(result['hit_at_5'],0.5)
        self.assertAlmostEqual(result['fact_recall_at_5'],0.75)
        self.assertAlmostEqual(result['mean_jaccard'],0.3)

if __name__=='__main__':unittest.main()

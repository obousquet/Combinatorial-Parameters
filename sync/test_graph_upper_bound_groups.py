"""Root-region classification uses full, established base affine reachability."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('make_graph', Path(__file__).resolve().parents[1]/'data/make_graph.py')
graph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(graph)


def relation(a, b, kind='larger', **extras):
    return dict(parameter_1_id=a, parameter_2_id=b, relationship_type=kind, status='established', **extras)


class RegionTests(unittest.TestCase):
    def test_affine_closure_and_exclusions(self):
        edges = [relation('E','a'), relation('a','both','larger_c'),
                 relation('S','b'), relation('b','both'),
                 relation('both','equal','equivalence'),
                 relation('S','a','log'),
                 relation('E','other')]
        edges[-1]['status'] = 'refuted'
        edges.append(relation('E','variant', variant='k=2'))
        vertices={'E','S','a','b','both','equal','other','variant'}
        self.assertEqual(graph.upper_bound_groups(edges,vertices,'E','S'),
                         dict(E=0,S=2,a=0,b=2,both=1,equal=1,other=3,variant=3))


if __name__ == '__main__':
    unittest.main()

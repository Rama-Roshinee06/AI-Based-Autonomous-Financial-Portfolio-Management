from algorithms.search import best_first_search
from algorithms.utility import ACTIONS, UtilityInputs, confidence, evaluate


def _grid():
    for m in (-1, -0.6, -0.2, 0, 0.3, 0.7, 1):
        for s in (-1, -0.5, 0, 0.4, 1):
            for r in (0, 0.25, 0.5, 0.75, 1):
                yield UtilityInputs(m, s, r)


def test_search_matches_exhaustive_argmax_everywhere():
    for inp in _grid():
        res = best_first_search(inp)
        best = max((evaluate(a, inp) for a in ACTIONS), key=lambda c: (c.utility, c.action == "HOLD"))
        assert abs(res.best_utility - best.utility) < 1e-3, inp
        assert evaluate(res.best_action, inp).utility >= best.utility - 1e-3


def test_search_is_more_efficient_than_exhaustive_somewhere():
    results = [best_first_search(i) for i in _grid()]
    assert all(r.term_evaluations <= r.exhaustive_evaluations for r in results)
    assert any(r.term_evaluations < r.exhaustive_evaluations for r in results)
    assert any(r.pruned_actions for r in results)


def test_search_result_structure():
    r = best_first_search(UtilityInputs(0.9, 0.7, 0.2))
    assert [c.action for c in r.candidates] == ["BUY", "HOLD", "SELL"]
    assert r.best_action == "BUY" and r.trace[-1].note.startswith("GOAL")
    assert r.nodes_generated >= 3 and r.nodes_expanded >= 4


def test_utility_formula_and_bounds():
    b = evaluate("BUY", UtilityInputs(0.5, 0.5, 0.5))
    assert abs(b.utility - (0.4 * .5 + 0.3 * .5 - 0.3 * .5)) < 1e-6
    assert best_first_search(UtilityInputs(5, -9, 3)).best_action in ACTIONS  # out-of-range inputs clamped
    c = confidence({"BUY": 0.5, "HOLD": 0.1, "SELL": -0.5}, "BUY")
    assert 0.5 < c < 1

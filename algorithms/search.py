"""Best-First Search over the action space {BUY, HOLD, SELL}.

State  : a partially evaluated candidate  (action, {terms evaluated so far}).
Root   : expands into 3 un-evaluated action nodes.
Heuristic h(node): known term values + optimistic upper bounds of unknown terms
                   (never underestimates the true utility -> admissible).
Frontier: priority queue ordered by highest h (ties -> conservative HOLD < SELL < BUY).
Expansion: evaluate the next term (market -> sentiment -> risk -> bias) of the best node.
Goal   : a node whose terms are all evaluated and that is popped first from the frontier.
Because h is optimistic, the first fully-evaluated node popped is the best action, and
actions whose bound falls below it are pruned without full evaluation.
"""
import heapq
import itertools
from typing import Dict, List
from algorithms.utility import ACTIONS, TERMS, UtilityInputs, evaluate, term_upper_bound, term_value
from models.schemas import SearchResult, SearchStep

TIE_PRIORITY = {"HOLD": 0, "SELL": 1, "BUY": 2}


def _h(action: str, known: Dict[str, float]) -> float:
    return sum(known[t] if t in known else term_upper_bound(action, t) for t in TERMS)


def best_first_search(inp: UtilityInputs) -> SearchResult:
    inp = inp.normalised()
    tick = itertools.count()
    frontier: list = []
    trace: List[SearchStep] = []
    generated = expanded = evals = 0

    for a in ACTIONS:
        heapq.heappush(frontier, (-_h(a, {}), TIE_PRIORITY[a], next(tick), a, {}))
        generated += 1
        trace.append(SearchStep(len(trace) + 1, a, 0, round(_h(a, {}), 4), "generated (optimistic bound)"))

    goal_action, goal_utility = None, None
    while frontier:
        neg_h, _, _, action, known = heapq.heappop(frontier)
        if len(known) == len(TERMS):
            goal_action, goal_utility = action, -neg_h
            trace.append(SearchStep(len(trace) + 1, action, len(known), round(-neg_h, 4), "GOAL: fully evaluated & best"))
            break
        term = TERMS[len(known)]
        val = term_value(action, term, inp)
        evals += 1
        expanded += 1
        new_known = {**known, term: val}
        h = _h(action, new_known)
        heapq.heappush(frontier, (-h, TIE_PRIORITY[action], next(tick), action, new_known))
        generated += 1
        trace.append(SearchStep(len(trace) + 1, action, len(new_known), round(h, 4),
                                f"expanded: evaluated {term} = {val:+.3f}"))

    pruned = sorted({n[3] for n in frontier if n[3] != goal_action})
    candidates = [evaluate(a, inp) for a in ACTIONS]  # exact values, for display
    return SearchResult(goal_action, round(goal_utility, 4), candidates, trace, generated, expanded,
                        evals, len(ACTIONS) * len(TERMS), pruned)

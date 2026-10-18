"""Deterministic tests for the Cain's Jawbone evidence-workbench."""
import unittest

from services.cain.jawbone import (
    candidate_transitions, feature_vector, narrator_clusters, normalize_pages, transition,
)

class CainBoundaryTests(unittest.TestCase):
    def test_fragment_lowercase_is_prioritized_but_not_certainty(self):
        result = transition(1, "I never understood why the flowers", 3, "were lying on his desk.")
        self.assertIn("incomplete_end_followed_by_lowercase", result.evidence)
        self.assertGreater(result.heuristic_score, 0.5)
        self.assertLessEqual(result.heuristic_score, 1.0)

    def test_sentence_boundary_is_not_zero(self):
        score = transition(4, "This is finished.", 8, "Another chapter starts.").heuristic_score
        self.assertGreater(score, 0)

    def test_candidates_have_no_self_edges_and_are_deterministic(self):
        pages = {2: "Another complete page.", 1: "The first page is", 3: "waiting for the evening."}
        a = candidate_transitions(pages, top=2)
        b = candidate_transitions(pages, top=2)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 6)
        self.assertTrue(all(x.from_page != x.to_page for x in a))

    def test_no_full_solution_with_missing_corpus(self):
        with self.assertRaises(ValueError):
            normalize_pages({"1": "Fragment"}, require_complete=True)
        self.assertEqual(len(normalize_pages({"1": "Fragment"})), 1)

    def test_rejects_invalid_and_duplicate_identifiers(self):
        with self.assertRaises(ValueError):
            normalize_pages({101: "unavailable"})
        with self.assertRaises(ValueError):
            normalize_pages({"1": "first", 1: "duplicate"})

    def test_stylometric_features_are_observations(self):
        features = feature_vector(3, "What, what! A tree.")
        self.assertEqual(features.page, 3)
        self.assertGreater(features.type_token_ratio, 0)
        self.assertLessEqual(features.type_token_ratio, 1.0)

    def test_cluster_requires_enough_pages_even_without_sklearn(self):
        with self.assertRaises(ValueError):
            narrator_clusters({1: "text", 2: "more text"}, n_clusters=6)

if __name__ == "__main__":
    unittest.main()

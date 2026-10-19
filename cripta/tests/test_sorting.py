import random
import unittest

from structures import sorting
from structures.sorting import (
    INSERTION,
    INSERTION_THEN_MERGE,
    MERGE,
    ComparisonCounter,
    algorithm_for,
    choose_algorithm,
    insertion_sort,
    merge_sort,
    shift_budget,
    sort,
)

ALGORITHMS = (insertion_sort, merge_sort, sort)


def is_ordered(values, reverse=False):
    for index in range(1, len(values)):
        if reverse and values[index - 1] < values[index]:
            return False
        if not reverse and values[index - 1] > values[index]:
            return False
    return True


class TestAlgorithms(unittest.TestCase):
    def test_empty_and_single(self):
        for algorithm in ALGORITHMS:
            self.assertEqual(algorithm([]), [])
            self.assertEqual(algorithm([7]), [7])

    def test_basic_cases(self):
        cases = (
            ([3, 1, 2], [1, 2, 3]),
            ([1, 2, 3], [1, 2, 3]),
            ([3, 2, 1], [1, 2, 3]),
            ([2, 2, 1, 1], [1, 1, 2, 2]),
            ([5, -1, 0, 5, 3], [-1, 0, 3, 5, 5]),
        )
        for algorithm in ALGORITHMS:
            for data, expected in cases:
                self.assertEqual(algorithm(data), expected)

    def test_does_not_modify_input(self):
        data = [3, 1, 2]
        for algorithm in ALGORITHMS:
            algorithm(data)
            self.assertEqual(data, [3, 1, 2])

    def test_reverse(self):
        for algorithm in ALGORITHMS:
            self.assertEqual(algorithm([1, 3, 2], reverse=True), [3, 2, 1])

    def test_stable(self):
        data = [(2, "a"), (1, "b"), (2, "c"), (1, "d"), (2, "e")] * 10
        for algorithm in ALGORITHMS:
            result = algorithm(data, key=lambda pair: pair[0])
            self.assertEqual([p[1] for p in result if p[0] == 1], ["b", "d"] * 10)
            self.assertEqual([p[1] for p in result if p[0] == 2], ["a", "c", "e"] * 10)

    def test_stable_in_reverse(self):
        data = [(1, "a"), (2, "b"), (1, "c"), (2, "d")] * 10
        for algorithm in ALGORITHMS:
            result = algorithm(data, key=lambda pair: pair[0], reverse=True)
            self.assertEqual([p[1] for p in result if p[0] == 2], ["b", "d"] * 10)

    def test_random_inputs_agree(self):
        generator = random.Random(2026)
        for size in (17, 100, 1000):
            data = [generator.randint(0, 50) for _ in range(size)]
            by_merge = merge_sort(data)
            self.assertTrue(is_ordered(by_merge))
            self.assertEqual(insertion_sort(data), by_merge)
            self.assertEqual(sort(data), by_merge)

    def test_strings_with_key(self):
        self.assertEqual(sort(["pera", "Ajo", "manzana"], key=str.lower), ["Ajo", "manzana", "pera"])

    def test_counter(self):
        counter = ComparisonCounter()
        insertion_sort([1, 2, 3, 4], counter=counter)
        self.assertEqual(counter.comparisons, 3)


class TestAutomaticChoice(unittest.TestCase):
    def test_small_uses_insertion(self):
        self.assertEqual(choose_algorithm(sorting.SMALL_THRESHOLD, 10**6), INSERTION)

    def test_large_unordered_uses_merge(self):
        size = sorting.SMALL_THRESHOLD * 10
        self.assertEqual(choose_algorithm(size, size // 2), MERGE)

    def test_large_nearly_sorted_uses_insertion(self):
        data = list(range(1000))
        data[10], data[11] = data[11], data[10]
        self.assertEqual(algorithm_for(data), INSERTION)

    def test_large_reversed_uses_merge(self):
        self.assertEqual(algorithm_for(list(range(1000, 0, -1))), MERGE)

    def test_threshold_is_32(self):
        self.assertEqual(sorting.SMALL_THRESHOLD, 32)
        counter = ComparisonCounter()
        sort(list(range(32, 0, -1)), counter=counter)
        self.assertEqual(counter.algorithm, INSERTION)
        sort(list(range(33, 0, -1)), counter=counter)
        self.assertEqual(counter.algorithm, MERGE)

    def test_reversed_data_is_sorted_when_asked_in_reverse(self):
        self.assertEqual(algorithm_for(list(range(1000, 0, -1)), reverse=True), INSERTION)



def rotated(size):
    half = size // 2
    return list(range(half, size)) + list(range(half))


class TestShiftBudget(unittest.TestCase):
    def test_budget_is_n_times_bits(self):
        self.assertEqual(shift_budget(1024), 1024 * 11)
        self.assertEqual(shift_budget(64), 64 * 7)

    def test_rotated_data_falls_back_to_merge(self):
        data = rotated(2048)
        self.assertEqual(algorithm_for(data), INSERTION)
        counter = ComparisonCounter()
        self.assertEqual(sort(data, counter=counter), list(range(2048)))
        self.assertEqual(counter.algorithm, INSERTION_THEN_MERGE)

    def test_fallback_costs_far_less_than_plain_insertion(self):
        data = rotated(2048)
        plain = ComparisonCounter()
        insertion_sort(data, counter=plain)
        adaptive = ComparisonCounter()
        sort(data, counter=adaptive)
        self.assertLess(adaptive.comparisons * 10, plain.comparisons)

    def test_nearly_sorted_stays_with_insertion(self):
        data = list(range(1000))
        for index in range(0, 1000, 100):
            data[index], data[index + 1] = data[index + 1], data[index]
        counter = ComparisonCounter()
        self.assertEqual(sort(data, counter=counter), list(range(1000)))
        self.assertEqual(counter.algorithm, INSERTION)

    def test_fallback_is_stable(self):
        keys = [key // 3 for key in rotated(3000)]
        data = [(keys[index], index) for index in range(len(keys))]
        counter = ComparisonCounter()
        result = sort(data, key=lambda pair: pair[0], counter=counter)
        self.assertEqual(counter.algorithm, INSERTION_THEN_MERGE)
        for index in range(1, len(result)):
            if result[index - 1][0] == result[index][0]:
                self.assertLess(result[index - 1][1], result[index][1])
        self.assertEqual(result, merge_sort(data, key=lambda pair: pair[0]))

    def test_fallback_in_reverse(self):
        data = list(reversed(rotated(2048)))
        counter = ComparisonCounter()
        self.assertEqual(sort(data, reverse=True, counter=counter), list(range(2047, -1, -1)))
        self.assertEqual(counter.algorithm, INSERTION_THEN_MERGE)


if __name__ == "__main__":
    unittest.main()

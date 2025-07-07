"""Split lists into a subset of tasks."""

from typing import Any, List


def split_list(target: List[Any], amount: int = 6) -> List[List[Any]]:
    """Take an arbitrary list and split into a set of lists.

    Args:
        target (List[Any]): the target list to split
        amount (int): the amount for each list to contain
    Returns:
        List[List[Any]]
    """
    return [target[x : x + amount] for x in range(0, len(target), amount)]

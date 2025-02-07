# -*- coding: utf-8 -*-
""" generic A-Star path searching algorithm """

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Dict, Iterable, Union, TypeVar, Generic
from math import inf as infinity
from operator import attrgetter
import heapq
from attrs import define
import openttd
from openttd.util import sync

__all__ = ["AStar"]


TilePath=openttd.tile.TilePath

from openttd._main import _async, test_mode

@define
class Cache:
    """Per-tile cached data, stored in TilePath"""

    gscore:float=0
    fscore:float=0
    in_todo:bool=False

    def __lt__(self, b: "SearchNode[T]") -> bool:
        """Natural order is based on the fscore value & is used by heapq operations"""
        if b is None:
            return False
        return self.fscore < b.fscore

    def __gt__(self, b: "SearchNode[T]") -> bool:
        """Natural order is based on the fscore value & is used by heapq operations"""
        if b is None:
            return False
        return self.fscore > b.fscore


class TileKeeper(dict):
    """A cache dict that returns existing content"""

    def get(self, tile: TilePath):
        if tile in self:
            return self[tile]
        self[tile] = tile
        return tile

    def set(self, tile: TilePath):
        self[tile] = tile
        return tile


class ToDo:
    """A heapq that keeps our not-yet-processed tiles."""
    def __init__(self) -> None:
        self.heap: list[TilePath] = []

    def push(self, item: SNType) -> None:
        item.cache.in_todo = True
        heapq.heappush(self.heap, item)

    def pop(self) -> SNType:
        item = heapq.heappop(self.heap)
        item.cache.in_todo = False
        return item

    def remove(self, item: SNType) -> None:
        idx = self.heap.index(item)
        item.cache.in_todo = False
        item = self.heap.pop()
        if idx < len(self.heap):
            self.heap[idx] = item
            # Fix heap invariants
            heapq._siftup(self.heap, idx)
            heapq._siftdown(self.heap, 0, idx)

    def __len__(self) -> int:
        return len(self.heap)


class AStar:
    """
    Algorithm to find the shortest way from A to B, A and B being a list of
    tiles.

    This class must be subclassed to be useful.
    """
    def estimate(self, current: TilePath) -> float:
        """
        Computes the estimated (rough) distance to the goal(s).

        This method must be implemented in a subclass.
        """
        raise NotImplementedError

    def neighbors(self, tile: TilePath) -> Iterable[tuple[TilePath,float]]:
        """
        For a given tile, returns (or yields) a list of its neighbors and
        the (incremental) cost for getting to each.

        This method must be implemented in a subclass.
        """
        raise NotImplementedError

    def is_goal(self, current: TilePath) -> bool:
        """
        Returns true when the algorithm should terminate.

        This method must be implemented in a subclass.
        """
        raise NotImplementedError

    def is_not_goal(self, current: TilePath) -> bool:
        """
        Returns true when the algorithm should skip this node.

        This is useful for recogniising dead ends, or station tiles that
        were approached from the wrong direction.

        The current tile is skipped but not marked as "done", thus
        approaching it from the correct direction still succeeds.

        The default is to return False.
        """
        return False

    @sync
    def run(self, start: TilePath|Iterable[TilePath]) -> TilePath | None:
        """
        Run the search.
        """
        todo = ToDo()
        self.cache = TileKeeper()
        if _async.get():
            raise RuntimeError("You *must* run the pathfinder in a subthread!")

        if isinstance(start,TilePath):
            start = [start]
        for tile in start:
            if self.is_goal(tile):
                return tile

            tile = self.cache.get(tile)
            tile.cache = Cache(gscore=0, fscore=self.estimate(tile))
            todo.push(tile)

        with test_mode():
            return self._run(todo)

    def _run(self, todo):
        while todo:
            openttd.test_stop()

            current = todo.pop()
            if self.is_goal(current):
                return current
            if self.is_not_goal(current):
                continue

            for candidate,cost in self.neighbors(current):
                candidate.cache = False
                neighbor = self.cache.get(candidate)
                if (cache := neighbor.cache) is None:
                    # Already fully processed.
                    continue

                gscore = current.cache.gscore + cost
                fscore = gscore + self.estimate(candidate)

                if cache is not False and cache.in_todo:
                    if cache.fscore <= fscore:
                        # the new path to this node isn't better
                        continue

                    # we have to remove the item from the heap, as its score has changed
                    todo.remove(neighbor)

                    # also we got there by some other way, so record that fact
                    neighbor = self.cache.set(candidate)

                neighbor.cache = Cache(gscore=gscore, fscore=fscore)
                todo.push(neighbor)

            current.cache = None

        return None


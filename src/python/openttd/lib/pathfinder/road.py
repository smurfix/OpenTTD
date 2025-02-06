# License of source: GPLv2
"""
A Road Pathfinder.

This road pathfinder tries to find a buildable / existing route for
road vehicles. You can changes the costs below using for example
roadpf.cost.turn = 30. Note that it's not allowed to change the cost
between consecutive calls to FindPath. You can change the cost before
the first call to FindPath and after FindPath has returned an actual
route. To use only existing roads, set cost.no_existing_road to
cost.max_cost.

This is a straight translation of Pathfinder.Road by truebrain,
(with some bug fixes).
"""
# /* $Id: main.nut 15101 2009-01-16 00:05:26Z truebrain $ */

from __future__ import annotations
from openttd.lib.astar import AStar

import openttd
import openttd.bridge
import openttd.tile
import openttd.vehicle
from openttd.error import TTDWrongTurn

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Literal

Turn=openttd.tile.Turn
Dir=openttd.tile.Dir
TilePath=openttd.tile.TilePath
Transport=openttd.tile.TransportType
Slope=openttd.tile.Slope
VT_Road=openttd.vehicle.Type.ROAD
BridgeType=openttd.bridge.BridgeType

class Info:
    author="OpenTTD NoAI Developers Team"
    name="Road"
    short_name="PFRO"
    description="An implementation of a road pathfinder"
    version=3
    date="2008-06-18"

class Node(TilePath):
    pass


class RoadPath(AStar):
    """
    A pathfinder for roads. It finds the shortest path from a set of source
    tiles to a set of goals. Both sources and goals can optionally include
    a direction which the path is supposed to take from/to them.

    Limitations:
    * The start tile can't be at a tunnel.
    * Bridges that start on flat land (e.g. to jump train tracks) are not considered.
    * There is no attempt to terraform for bridges or tunnels.

    You can set these attributes (or override them in a subclass):

    @max_cost: The maximum cost for a route.
    @cost_tile: The cost per tile. The default is 100. All other costs are added to this.
    @cost_no_existing_road: Cost (per tile) for building a new road.
    @cost_turn: Cost for turning, to encourage straight roads. The default is 100.
    @cost_slope: Extra cost for sloped roads. (Up or down doesn't matter.)
    @cost_bridge: Penalty for building a bridge (total).
    @cost_bridge_per_tile: Penalty for building a bridge (per tile)
    @cost_tunnel: Penalty for building a tunnel (total).
    @cost_tunnel_per_tile: Penalty for building a tunnel (per tile)
    @cost_coast: Extra cost for a coast tile (they slow traffic down).
    max_bridge_length: Max length for bridges.
    max_tunnel_length: Max length for tunnels.
    """

    max_cost = 10000000
    cost_tile = 100
    cost_no_existing_road = 40
    cost_turn = 50
    cost_slope = 300
    cost_bridge = 200
    cost_tunnel = 50
    cost_bridge_per_tile = 150
    cost_tunnel_per_tile = 120
    cost_coast = 20
    max_bridge_length = 10
    max_tunnel_length = 20

    def __init__(self, sources:Iterable[Tile], goals:Iterable[Tile], **cfg):
        self.sources = sources
        self.goals = set(goals)
        for k,v in cfg:
            if not isinstance(getattr(self,k,None),int):
                raise ValueError(f"Unknown attribute: {k !r}")
            setattr(self,k,v)

    def run(self) -> TilePath:
        """
        Main code. You *must* Run in a subthread without arguments.
        """
        return super().run(self.sources)

    def is_goal(self, dest):
        "Check for goal tiles that were reached from the correct direction."
        for goal in self.goals:
            if dest.xy != goal.xy:
                continue
            if goal.d == Dir.SAME or goal.d.back == dest.d:
                return True
        return False

    def is_not_goal(self, dest):
        "Check for goal tiles that were reached from the wrong direction."
        for goal in self.goals:
            if dest.xy != goal.xy:
                continue
            if goal.d != Dir.SAME and goal.d.back != dest.d:
                return True
        return False

    @staticmethod
    def slopes_for_bridge(end_a, end_b):
        direction = end_b % end_a
        def is_sloped(slope, direction):
            # There is no slope *if* the land rises in the direction you
            # take when exiting the bridge. (Bug in original)
            if direction == Dir.NE:
                return slope not in (Slope.N, Slope.E, Slope.NE)
            if direction == Dir.SE:
                return slope not in (Slope.S, Slope.E, Slope.SE)
            if direction == Dir.SW:
                return slope not in (Slope.S, Slope.W, Slope.SW)
            if direction == Dir.NW:
                return slope not in (Slope.N, Slope.W, Slope.NW)
            return 1
        return is_sloped(end_a.slope, direction) + is_sloped(end_b.slope,direction.back)

    def cost(self, prev, tile):
        """Incremental cost to go to new_tile"""
        may_need_build = True

        if prev is None:
            # first node of a path
            return 0

        # If the new tile is an existing bridge / tunnel start,
        # we came from the other end.
        if tile.has_bridge:
            return tile.d_manhattan(prev) * self.cost_tile + self.slopes_for_bridge(tile, prev) * self.cost_slope

        if tile.has_tunnel:
            return tile.d_manhattan(prev) * self.cost_tile

        # If the two tiles are more than 1 tile apart, the pathfinder wants a
        # bridge or tunnel to be built.

        if tile.d_manhattan(prev) > 1:
            # Check if we should build a bridge or a tunnel. If it's
            # a tunnel then it has a valid destination *and* tunneling the
            # other end gets back to us.
            try:
                dest = tile.tunnel_dest
            except ValueError:
                dest = None
            if dest is not None and dest == prev:
                cost = self.cost_tunnel + tile.d_manhattan(prev) * (self.cost_tile + self.cost_tunnel_per_tile)
            else:
                cost = self.cost_bridge + tile.d_manhattan(prev) * (self.cost_tile + self.cost_bridge_per_tile) + self.slopes_for_bridge(tile, prev) * self.cost_slope

        else:
            cost = self.cost_tile if tile.dist else 0
            may_need_build = True

        # Next, account for turns.
        if tile.d != prev.d:
            cost += self.cost_turn

            # Check for two turns in succession. We make these a bit more
            # expensive so we don't end up with a zigzag pattern.

            if tile.prev_turn is not None and tile.prev_turn.prev_turn is not None and tile.prev_turn.dist <= 2 and tile.prev_turn.prev_turn.d is not Dir.SAME:
                if tile.prev_turn.d-tile.d == tile.prev_turn.prev_turn.d-tile.prev_turn.d:
                    # Tight U-turns get even more penalized.
                    cost += self.cost_turn*3
                else:
                    cost += self.cost_turn//2

        if tile.is_coast:
            cost += self.cost_coast

        if prev.prev is not None and not prev.has_bridge and not prev.has_tunnel and self.is_sloped_road(prev.prev,prev,tile):
            cost += self.cost_slope

        if not prev.has_road_to(tile):
            cost += self.cost_no_existing_road

        return cost

    def estimate(self, tile):
        for g in self.goals:
            if tile.t == g:
                # We reached the tile from the wrong direction.
                if tile.d == g.d.back:
                    # do a loop
                    return self.cost_tile*6+self.cost_turn*4
                else:
                    # do three lefts
                    return (self.cost_tile+self.cost_turn)*3
        def turn_cost(goal):
            if goal.d is Dir.SAME or tile.d is Dir.SAME: # or goal.t == tile.t:
                return 0
            return self.cost_turn*abs(tile.d.value - tile.step_to(goal,diagonal=False).value)//2

        return min(self.cost_tile * tile.d_manhattan(goal) + turn_cost(goal) for goal in self.goals)

    def neighbors(self, tile):
        def _cost(new_tile):
            return new_tile,self.cost(tile,new_tile)

        # self.max_cost is the maximum path cost;
        # if we go over it, the path isn't valid.
        if tile.cache.fscore > self.max_cost:
            return

        if (tile.has_bridge or tile.has_tunnel) and tile.has_transport(Transport.ROAD):
            # We're at the exit of a bridge/tunnel.
            next_tile = tile+Turn.S
            # test whether we can step off the bridge/tunnel
            if tile.has_road_to(next_tile) or next_tile.is_buildable or next_tile.is_road:
                yield _cost(next_tile)
            return

        # If you compare this code to the original, you might wonder what
        # happened to the next two sections. Surprise: they are superfluous.

        for turn in (
                # If not a start tile we can go straight, or turn right or left.
                (Turn.S,Turn.RR,Turn.LL) if tile.prev_turn is not None else

                # If the start direction doesn't matter, use any direction.
                (Dir.NE,Dir.SE,Dir.NW,Dir.SW) if tile.d == Dir.SAME else

                # If it does, go in that direction (only).
                (tile.d,)
                ):
            next_tile = tile+turn

            # We use the destination if one of the following applies:

            if tile.has_road_to(next_tile):
                # 1) There already is a connections between the current tile and the next tile.
                yield _cost(next_tile)
            elif (next_tile.is_buildable or next_tile.is_road) and (tile.prev is None or tile.can_build_road_parts(tile.prev.t, next_tile.t)) and tile.build_road_to(next_tile.t):
                # 2) We can build a road to the next tile.
                yield _cost(next_tile)
            elif (length := self.check_tunnel_bridge(tile, next_tile)):
                # 3) The next tile is the entrance of a tunnel / bridge in that direction.
                yield _cost(tile+next_tile.d*length)  # exit of the tunnel

        # Bridges and tunnels
        if tile.prev is None:
            # The start node can't be a tunnel.
            return

        # Bridges will only be build starting on non-flat tiles for
        # performance reasons. (XXX but we want to cross railways ..?)
        slope = tile.slope
        if slope is Slope.FLAT:
            return

        # Get all bridges and tunnels that can be build from the
        # current tile.
        # Tunnels will only be build if no terraforming is needed on both ends.
        # (XXX well …)

        for i in range(2, self.max_bridge_length):
            bridges = BridgeType.List(i + 1)
            if bridges:
                try:
                    dest = tile+tile.d*(i+1)
                except ValueError:
                    break
                if bridges.any.build(VT_Road, tile.t,dest.t):
                    yield _cost(dest)

        if slope not in {Slope.SW,Slope.NW,Slope.SE,Slope.NE}:
            return
        try:
            dest = tile.tunnel_dest
            src = dest.tunnel_dest
        except ValueError:
            pass
        else:
            tunnel_length = tile.d_manhattan(dest)
            try:
                prev_tile = tile + dest%tile
            except TTDWrongTurn:
                return
            if src == tile and tunnel_length >= 2 and prev_tile.xy == tile.prev.xy and tile.build_tunnel(VT_Road):
                yield _cost(tile+tile.d*tunnel_length)

    @staticmethod
    def is_sloped_road(start, middle, end):
        NW = 0  # Set to true if we want to build a road to / from the north-west
        NE = 0  # Set to true if we want to build a road to / from the north-east
        SW = 0  # Set to true if we want to build a road to / from the south-west
        SE = 0  # Set to true if we want to build a road to / from the south-east

        # both point towards the middle. This is intentional.
        da = start%middle
        db = end%middle
        NW = Dir.NW in (da,db)
        NE = Dir.NE in (da,db)
        SE = Dir.SE in (da,db)
        SW = Dir.SW in (da,db)

        # If there is a turn in the current tile, it can't be sloped.
        if (NW or SE) and (NE or SW):
            return False

        # A road on a steep slope is always sloped.
        slope = middle.slope
        if slope.is_steep:
            return True

        # If only one corner is raised, the road is sloped.
        if slope in {Slope.N,Slope.S,Slope.E,Slope.W}:
            return True

        if NW and slope in (Slope.NW, Slope.SE):
            return True
        if NE and slope in (Slope.NE, Slope.SW):
            return True

        return False

    @staticmethod
    def check_tunnel_bridge(current, new) -> Literal[False]|int:
        """
        Check if the next tile is the start of a bridge/tunnel
        that goes in the correct direction.
        """
        if new.has_bridge:
            other = new.bridge_dest
        elif new.has_tunnel:
            other = new.tunnel_dest
        else:
            return False
        if current%new != new%other:
            return False
        return current.d_manhattan(other)


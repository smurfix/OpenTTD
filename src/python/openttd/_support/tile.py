#
# This file is part of OpenTTD.
# OpenTTD is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, version 2.
# OpenTTD is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with OpenTTD. If not, see <http://www.gnu.org/licenses/>.
#

"""
This module elaborates on tiles.
"""

from __future__ import annotations

import _ttd
import openttd
import enum
from attrs import define,field

_offsets = (
    ( 0,  0), # SAME
    (-1, -1), # N
    (-1,  0), # NE
    (-1,  1), # E
    ( 0,  1), # SE
    ( 1,  1), # S
    ( 1,  0), # SW
    ( 1, -1), # W
    ( 0, -1), # NW
)

class Dir(enum.Enum):
    """
    Encodes a compass direction. You can add a direction to a tile to get the next
    tile in that direction. You can add a Turn to a direction to rotate it.
    """
    SAME=-1
    N=0
    NE=1
    E=2
    SE=3
    S=4
    SW=5
    W=6
    NW=7

    @property
    def xy(self):
        """
        Returns an x+y tuple to add to a tile.
        """
        return _offsets[self.value+1]

    @property
    def back(self):
        """reverse"""
        if self is Dir.SAME:
            return self
        return Dir((self.value+4) % 8)

    def __add__(self, d):
        "direction plus turn is direction"
        if isinstance(d,(Turn,_ttd.enum.DirDiff)):
            return type(self)((self.value + d.value) % 8)

        return NotImplemented

    def __radd__(self, t):
        if isinstance(t,Tile):
            off=_offsets[self.value+1]
            return type(t)(t.x+off[0], t.y+off[1])
        return NotImplemented

    def __sub__(self, d):
        """
        direction minus direction is turn;
        direction minus turn is direction.
        """
        if isinstance(d,Dir):
            if d is Dir.SAME:
                return self
            if self is Dir.SAME:
                return d.back
            return type(self)((self.value-d.value)%8)

        if isinstance(d,(Turn,_ttd.enum.DirDiff)):
            return type(self)((self.value - d.value) % 8)

        return NotImplemented

    def __mul__(self, i):
        return DirHop(self,i)

_offset_ids = { v:Dir(k-1) for k,v in enumerate(_offsets) }

class DirHop:
    """a direction that travels multiple tiles"""
    def __init__(self,d,n):
        self.d = d
        self.n = n
    def xy(self):
        d=self.d.xy
        return (d[0]*self.n, d[1]*self.n)
    def __mul__(self, n):
        return type(self)(self.d,self.n*n)
    __rmul__=__mul__

    def __add__(self,td):
        if isinstance(td,Dir):
            if td==self.d:
                return type(self)(self.d,self.n+1)
            elif td == self.d.back:
                return type(self)(self.d,self.n-1)
        return NotImplemented

class Turn(enum.Enum):
    """
    Encodes a relative direction. (You can add them.)

    Attributes are S (same), B (back), L/R (45°) and LL/RR(90°).
    """
    S=0
    R=1
    RR=2
    BR=3
    B=4
    BL=5
    LL=6
    L=7

    def __add__(self, d):
        if isinstance(d,(Turn,_ttd.enum.DirDiff)):
            return type(self)((self.value + d.value) % 8)
        return NotImplemented


class Tile:
    def __init__(self, x,y):
        self._ = _ttd.support.Tile_(x,y)

    @property
    def x(self):
        return self._.x
    @property
    def y(self):
        return self._.y
    @property
    def xy(self):
        return (self._.x,self._.y)
    def __str__(self):
        return f"({self.x},{self.y})"

    def __repr__(self):
        return f"Tile({self.x},{self.y})"

    def __add__(self, x):
        """Tile plus some x-y offset returns a tile.
        Tile plus direction returns a new Tile.
        """
        if isinstance(x,(list,tuple)):
            return Tile(self.x+x[0], self.y+x[1])
        if isinstance(x,(Dir,_ttd.enum.Direction)):
            x=x.xy
            return Tile(self.x+x[0], self.y+x[1])
        if x is Dir.SAME:
            return self
        return NotImplemented

    def __matmul__(self, x):
        """Tile @ direction returns a TileDir.
        """
        if isinstance(x,(Dir,_ttd.enum.Direction)):
            return TileDir(self, x)+x
        return NotImplemented

    def __sub__(self, t:Tile|tuple[int,int]) -> Tile|tuple[int,int]:
        """Tile minus some x-y offset returns a tile, and vice versa.
        Subtracting a direction returns a tile.
        """
        if isinstance(t,(list,tuple)):
            return Tile(self.x-t[0], self.y-t[1])
        if isinstance(t,Tile):
            return (self.x-t.x, self.y-t.y)
        if isinstance(t,(Dir,_ttd.enum.Direction)):
            d=t.xy
            return Tile(self.x-d[0], self.y-d[1])
        return NotImplemented

    def __mod__(self, t:Tile) -> Dir:
        """a%b returns one step of the direction you need to add to A to get to B.
        Diagonal movement is first, when necessary.
        """
        dx = t.x-self.x
        dy = t.y-self.y
        if dx==0 and dy==0:
            return Dir.SAME
        try:
            return _offset_ids[(dx,dy)]
        except KeyError:
            # Longer. Move diagonally until rectified.
            dx = max(min(dx,1),-1)
            dy = max(min(dy,1),-1)
            return _offset_ids[(dx,dy)]

    def step_to(self, t:Tile, diagonal:bool|None=None) -> Dir:
        """Get one step towards @t from here.

        @diagonal can be None (default: no diagonals), False (straight line
        first) or True (diagonal first, same as a%b).
        """
        dx = t.x-self.x
        dy = t.y-self.y
        if dx==0 and dy==0:
            return Dir.SAME
        if dx and dy and (diagonal is None or diagonal is False and abs(dx) != abs(dy)):
            # When we can eventually go diagonally, work on the longer side
            # first. Otherwise do the shorter side first because if not
            # we'd go zigzag.
            if (diagonal is None) == (abs(dx)<abs(dy)):
                dy=0
            else:
                dx=0
        dx = max(min(dx,1),-1)
        dy = max(min(dy,1),-1)
        return _offset_ids[(dx,dy)]

    @property
    def is_buildable(self) -> bool:
        return openttd.tile.is_buildable(self._)
    def is_buildable_rect(self, w:int, h:int) -> bool:
        return openttd.tile.is_buildable_rectangle(self._, w, h)
    @property
    def is_sea(self) -> bool:
        return openttd.tile.is_sea_tile(self._)
    @property
    def is_river(self) -> bool:
        return openttd.tile.is_river_tile(self._)
    @property
    def is_water(self) -> bool:
        return openttd.tile.is_water_tile(self._)
    @property
    def is_coast(self) -> bool:
        return openttd.tile.is_coast_tile(self._)
    @property
    def is_station(self) -> bool:
        return openttd.tile.is_station_tile(self._)
    @property
    def has_tree(self) -> bool:
        return openttd.tile.has_tree_on_tile(self._)
    @property
    def is_farm(self) -> bool:
        return openttd.tile.is_farm_tile(self._)
    @property
    def is_rock(self) -> bool:
        return openttd.tile.is_rock_tile(self._)
    @property
    def is_rough(self) -> bool:
        return openttd.tile.is_rough_tile(self._)
    @property
    def is_snow(self) -> bool:
        return openttd.tile.is_snow_tile(self._)
    @property
    def is_desert(self) -> bool:
        return openttd.tile.is_desert_tile(self._)
    @property
    def is_bridge(self) -> bool:
        return openttd.bridge.is_bridge_tile(self._)
    @property
    def bridge_dest(self) -> Tile:
        return openttd.bridge.get_other_bridge_end(self._)
    @property
    def is_tunnel(self) -> bool:
        return openttd.tunnel.is_tunnel_tile(self._)
    @property
    def tunnel_dest(self) -> Tile:
        return openttd.tunnel.get_other_tunnel_end(self._)
    @property
    def terrain(self) -> openttd.tile.TerrainType:
        return openttd.tile.get_terrain_type(self._)
    def has_road_to(self, other:Tile):
        return openttd.road.has_road_to(self._, other._)

    def build_road_to(self, other:Tile, full:bool=False, oneway:bool=False):
        # it's rather silly to split that into four, only for
        # script_road.cpp to piece it together again. Oh well. TODO.
        r = openttd.road
        p = (r.build_one_way_road_full if oneway else r.build_road_full) if full else (r.build_one_way_road if oneway else r.build_road)
        return p(self._, other._)

    @property
    def slope(self) -> openttd.tile.Slope:
        return openttd.tile.get_slope(self._)
    @property
    def min_height(self) -> int:
        return openttd.tile.get_min_height(self._)
    @property
    def max_height(self) -> int:
        return openttd.tile.get_max_height(self._)
    def corner_height(self, corner: openttd.tile.Corner):
        return openttd.tile.get_corner_height(self._, corner)
    @property
    def owner(self) -> CompanyID:
        return openttd.tile.get_owner(self._)
    def has_transport(self, ttype: openttd.tile.TransportType):
        return openttd.tile.has_transport_type(self._, ttype)
    def cargo_acceptance(self, cargo_type: openttd.cargo.Cargo, width: int, height: int, radius: int) -> int:
        return openttd.tile.get_cargo_acceptance(self._, cargo_type, width,height,radius)
    def cargo_production(self, cargo_type: openttd.cargo.Cargo, width: int, height: int, radius: int) -> int:
        return openttd.tile.get_cargo_production(self._, cargo_type, width,height,radius)
    def raise_(self, slope:openttd.tile.Slope) -> Awaitable:
        """*sigh* Python syntax"""
        return openttd.tile.raise_tile(self._, slope)
    def lower(self, slope:openttd.tile.Slope) -> Awaitable:
        return openttd.tile.lower_tile(self._, slope)
    def level_to(self, tile: Tile) -> Awaitable:
        return openttd.tile.level_tiles(self._, tile)
    def demolish(self) -> Awaitable:
        return openttd.tile.demolish_tile(self._)
    def plant_tree(self) -> Awaitable:
        return openttd.tile.plant_tree(self._)
    def plant_tree_rect(self, width: int, height: int) -> Awaitable:
        return openttd.tile.plant_tree_rectangle(self._, width, height)
    def is_within_town(self, town: int):
        """test influence"""
        return openttd.tile.is_within_town_influence(self._, town)
    @property
    def authority_town(self):
        return openttd.tile.get_town_authority(self._)
    @property
    def closest_town(self):
        return openttd.tile.get_closest_town(self._)

    # don't call out to openttd for this
    def d_manhattan(self, tile: Tile) -> int:
        return abs(self.x-tile.x) + abs(self.y-tile.y)
    def d_square(self, tile: Tile) -> int:
        return (self.x-tile.x)**2 + (self.y-tile.y)**2
    def d_max(self, tile: Tile) -> int:
        return max(abs(self.x-tile.x), abs(self.y-tile.y))
    def d_max_manhattan(self, tile: Tile) -> int:
        ax = abs(self.x-tile.x)
        ay = abs(self.y-tile.y)
        return ax+ay+max(ax,ay)



@define
class TileDir:
    """
    A tile with a path, direction, and cache for the cost function.
    """
    t:Tile=field()
    d:Dir=field()
    _prev:TileDir|None=field(default=None)
    dist:int=field(default=0)
    cache:Any=None

    def __attrs_post_init__(self):
        assert not isinstance(self.t,int)

    @property
    def _(self):
        return self.t._

    @property
    def x(self):
        return self.t.x

    @property
    def y(self):
        return self.t.y

    @property
    def xy(self):
        return self.t.xy

    def __repr__(self):
        return f"TDir({self.t} {self.d.name}*{self.dist})"

    def __eq__(self, other:Tile|TileDir):
        """Compare location and direction"""
        if self.t.x != other.x:
            return False
        if self.t.y != other.y:
            return False
        if self.d is None or (d := getattr(other,"d")) is None:
            return True
        return self.d == d

    def __cmp__(self, other:TileDir):
        return self.cache.__cmp__(other.cache)

    def __add__(self, x):
        # go straight ahead?
        if x is Turn.S:
            return TileDir(self.t+self.d, self.d, prev=self._prev, dist=self.dist+1)

        # No, turn
        if isinstance(x,(Turn,_ttd.enum.DirDiff)):
            d=self.d+x
            return TileDir(Tile(self.x,self.y)+d, d, prev=self, dist=1)

        if isinstance(x,(Dir,_ttd.enum.Direction)):
            if x==self.d:
                return TileDir(self.t+self.d, self.d, prev=self._prev, dist=self.dist+1)
            # otherwise turn
            return TileDir(Tile(self.x,self.y)+x, x, prev=self, dist=1)

        return NotImplemented

    @property
    def prev(self):
        """Return the adjacent previous tile """
        if self.dist:
            return self.t-self.d
        if self._prev is None:
            return None
        return self._prev.prev

    def __iter__(self):
        """Iterate the path, starting at the beginning."""
        if self._prev is not None:
            yield from self._prev
        yield self



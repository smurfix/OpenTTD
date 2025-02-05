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

import openttd
import _ttd
import enum
import os
from attrs import define,field
from .util import extension_of, PlusSet
from ._util import with_
from .error import TTDError, TTDWrongTurn

import typing
from typing import overload

if typing.TYPE_CHECKING:
    from openttd.town import Town
    from openttd.road import RoadType
    from typing import Callable,Self


_offsets = (
    (-1, -1), # N
    (-1,  0), # NE
    (-1,  1), # E
    ( 0,  1), # SE
    ( 1,  1), # S
    ( 1,  0), # SW
    ( 1, -1), # W
    ( 0, -1), # NW
)

_arrows = "↑↗→↘↓↙←↖🡱🡵🡲🡶🡳🡷🡰🡴"
_places = "○●"

@extension_of(_ttd.enum.Direction)
class Dir:
    """
    Encodes a compass direction. You can add a direction to a tile to get the next
    tile in that direction. You can add a Turn to a direction to rotate it.
    """
    @property
    def xy(self):
        """
        Returns an x+y tuple to add to a tile.
        """
        return _offsets[self.value]

    @property
    def back(self):
        """reverse"""
        return Dir((self.value+4) % 8)
    back1=back

    # DirJump compatibility
    @property
    def d(self) -> Self:
        return self

    @property
    def jump(self) -> bool:
        return False

    @property
    def n(self):
        return 1

    def __add__(self, d:Turn):
        "direction + turn is a new direction"
        if isinstance(d,Turn):
            return type(self)((self.value + d.value) % 8)

        return NotImplemented

    def __radd__(self, t) -> Tile:
        "Tile + direction = tile"
        if isinstance(t,Tile):
            off=_offsets[self.value]
            return type(t)(t.x+off[0], t.y+off[1])

        return NotImplemented

    def __sub__(self, d):
        """
        direction minus direction is turn;
        direction minus turn is direction.
        """
        if isinstance(d,Dir):
            return Turn((self.value-d.value)%8)

        if isinstance(d,Turn):
            return type(self)((self.value - d.value) % 8)

        return NotImplemented

    def __mul__(self, i):
        return DirJump(self,i)

class DirSame:
    name="SAME"
    pass
DirSame = DirSame()
Dir.SAME = DirSame


if "PY_OTTD_STUB_GEN" in os.environ:
    _offset_ids = { }
else:
    _offset_ids = { v:Dir(k) for k,v in enumerate(_offsets) }

@define
class DirJump:
    """A direction that travels multiple tiles.
    Used for bridges and tunnels. (No teleporting. Sorry.)
    """
    d:Dir
    n:int
    jump:bool=field(default=True)

    @property
    def back(self):
        """Back to where we came from"""
        return DirJump(self.d.back,self.n)

    @property
    def back1(self):
        """Back one step"""
        return self.d.back

    @property
    def xy(self):
        """x,y offset of this step"""
        d=self.d.xy
        return (d[0]*self.n, d[1]*self.n)

    def __repr__(self):
        return f"{self.d}*{self.n}"

    def __mul__(self, n):
        return type(self)(self.d,self.n*n)

    __rmul__=__mul__

    def __add__(self,td):
        """Add one more step"""
        if isinstance(td,Dir):
            if td==self.d:
                return type(self)(self.d,self.n+1)
            elif td == self.d.back:
                return type(self)(self.d,self.n-1)
        return NotImplemented

    def __radd__(self, t):
        """Movement: Tile+DirJump"""
        if isinstance(t,Tile):
            off=_offsets[self.d.value]
            return type(t)(t.x+off[0]*self.n, t.y+off[1]*self.n)
        return NotImplemented

    def __rsub__(self, t):
        """Movement back: Tile-DirJump"""
        if isinstance(t,Tile):
            off=_offsets[self.d.value]
            return type(t)(t.x-off[0]*self.n, t.y-off[1]*self.n)
        return NotImplemented


@extension_of(_ttd.script.tile.Slope)
class Slope:
    """
    Encodes the direction of a slope and how steep it is.
    """
    @property
    def is_steep(self) -> bool:
        return bool(self.value & self.STEEP.value)

    def can_build_road_parts(start:Dir, end:Dir, *existing:Dir):
        """
        Test whether a road from @start to @end is possible given this
        slope and @existing other road connections.
        """
        return unless(-1, _ttd.script.road.can_build_connected_road_parts,self,[x.index for x in existing], start.index,end.index)




@extension_of(_ttd.script.tile.TransportType)
class TransportType:
    """
    Encodes the type of a transport
    """

@extension_of(_ttd.script.tile.BuildType)
class BuildType:
    """
    Encodes the type for (re)building things

    used mainly for retrieving cost
    """
    @property
    def cost(self):
        return _ttd.script.tile.get_build_cost(self)


@extension_of(_ttd.script.tile.TerrainType)
class TerrainType:
    """
    Encodes the type for (re)building things

    used mainly for retrieving cost
    """


@extension_of(_ttd.support.DirDiff)
class Turn: # (enum.IntEnum):
    """
    Encodes a relative direction. (You can add them.)

    Attributes are S (same), B (back), L/R (45°) and LL/RR(90°).
    """
    def __add__(self, d):
        if isinstance(d,Turn):
            return type(self)((self.value + d.value) % 8)
        return NotImplemented


class Tiles(PlusSet["Tile"]):
    """
    This class represents a set of tiles. Various generators and a simple
    filter system make them reasonably easy to use.

    NB: unlike all other collective functions, instantiating this class directly
    returns an empty set.
    """
    pass


@extension_of(_ttd.support.Tile_)
class Tile[Collection:Tiles]:
    Tiles:Collection = Tiles

    def __new__(cls, x,y=None):
        if y is not None:
            try:
                return _ttd.support.Tile_(x,y)
            except TypeError:
                if x<0:
                    raise ValueError("x coord out of bounds") from None
                if y<0:
                    raise ValueError("y coord out of bounds") from None
                raise
        elif isinstance(x,TilePath):
            return x.t
        elif isinstance(x,Tile):
            return x
        elif isinstance(x,int):
            return _ttd.support.Tile_(x)
        else:
            raise ValueError(f"Tile: no creator for {x}")

    @property
    def xy(self):
        return (self.x,self.y)

    def __str__(self):
        return f"({self.x},{self.y})"

    def __hash__(self):
        return self.value

    def __eq__(self, other:Tile):
        if isinstance(other,TilePath):
            other = other.t
        return self.value == other.value

    def __repr__(self):
        return f"Tile({self.x},{self.y})"

    @overload
    def __add__(self, x: Literal[Dir.SAME]) -> Self: ...

    @overload
    def __add__(self, x: Tuple[int,int]) -> Self: ...

    @overload
    def __add__(self, x: Dir) -> Self: ...

    @overload
    def __add__(self, x: DirJump) -> TilePath: ...

    def __add__(self, x):
        """Tile plus some x-y offset returns a tile.
        Tile plus direction returns a new Tile.
        Tile plus step (DirJump) returns a TilePath.
        """
        if x is Dir.SAME:
            return self
        if isinstance(x,(list,tuple)):
            return Tile(self.x+x[0], self.y+x[1])
        if isinstance(x,Dir):
            xy=x.xy
            return Tile(self.x+xy[0], self.y+xy[1])
        if isinstance(x,DirJump):
            xy=x.xy
            return TilePath(Tile(self.x+xy[0], self.y+xy[1]), x.d, dist=x.n, jump=x.jump)
        return NotImplemented

    def __matmul__(self, x):
        """Tile @ direction returns a TilePath.
        """
        if isinstance(x,(Dir,_ttd.enum.Direction)):
            return TilePath(self, x)+x
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
    def content_str(self) -> str:
        class RR(list):
            def __getattr__(self, k):
                self.append(k)
        R=RR()

        if self.is_road:
            R.road
        if self.is_rail:
            R.rail
        if self.is_river:
            R.river
        if self.is_water:
            R.water
        if self.is_sea:
            R.sea
        if self.is_coast:
            R.coast
        if self.is_farm:
            R.farm
        if self.has_tree:
            R.tree
        if self.has_rock:
            R.rock
        if self.in_snow:
            R.snow
        if self.in_desert:
            R.desert
        if self.is_station:
            R.station
        # TODO check for waypoint, there are different types ...
        if self.has_bridge:
            R.bridge
        if self.has_tunnel:
            R.tunnel
        if self.is_buildable:
            R.can_build

        if not R:
            return "?"
        return " ".join(R)

    @property
    def is_buildable(self) -> bool:
        return _ttd.script.tile.is_buildable(self)

    def is_buildable_rect(self, w:int, h:int) -> bool:
        return _ttd.script.tile.is_buildable_rectangle(self, w, h)

    @property
    def is_sea(self) -> bool:
        return _ttd.script.tile.is_sea_tile(self)

    @property
    def is_river(self) -> bool:
        return _ttd.script.tile.is_river_tile(self)

    @property
    def is_water(self) -> bool:
        return _ttd.script.tile.is_water_tile(self)

    @property
    def is_coast(self) -> bool:
        return _ttd.script.tile.is_coast_tile(self)

    @property
    def is_station(self) -> bool:
        return _ttd.script.tile.is_station_tile(self)

    def has_waypoint(self, type_: WaypointType) -> bool:
        return _ttd.script.waypoint.has_waypoint_type(self, type_)

    @property
    def has_station(self) -> bool:
        id = _ttd.script.station.get_station_id(self)
        return _ttd.script.station.is_valid_station(id)

    @property
    def station(self) -> Station:
        id = _ttd.script.station.get_station_id(self)
        if not _ttd.script.station.is_valid_station(id):
            raise ValueError(f"not a station at {self.xy}")
        return Station(id)

    @property
    def waypoint(self) -> Waypoint:
        id = _ttd.script.station.get_waypoint_id(self)
        return Waypoint(id)

    @property
    def is_road_station(self) -> bool:
        return _ttd.script.road.is_road_station_tile(self)

    @property
    def is_drivethru_road_station(self) -> bool:
        return _ttd.script.road.is_drive_through_road_station_tile(self)

    @property
    def is_road_depot(self) -> bool:
        return _ttd.script.road.is_road_depot_tile(self)

    @property
    def road_depot_front(self) -> Tile:
        return  _ttd.script.road.get_road_depot_front_tile(self)

    @property
    def road_station_front(self) -> Tile:
        return  _ttd.script.road.get_road_station_front_tile(self)

    @property
    def road_station_back(self) -> Tile:
        return  _ttd.script.road.get_drive_through_back_tile(self)

    def is_road_type(self, type:RoadType) -> bool:
        return _ttd.script.road.is_road_depot_tile(self)

    def build_road_depot(self, front:Tile|Dir) -> None:
        if isinstance(front,Dir):
            front = self+front
        return with_(None, _ttd.script.road.buil_road_depot,self,front)

    def build_road_station(self, front:Tile|Dir, type: RoadType, drive_through:bool=False, station: Station|None=None) -> None:
        if isinstance(front,Dir):
            front = self+front
        if station is None:
            station = openttd._.Station.NEW
        return with_(None, _ttd.script.road.build_drive_through_road_station if drive_through else _ttd.script.road.build_road_station,self,front,station)

    def remove_road(self, full:bool=False) -> None:
        return with_(None, _ttd.script.road.remove_road_full if full else _ttd.script.road.remove_road)

    def remove_road_depot(self) -> None:
        return with_(None,_ttd.script.road.remove_road_depot)

    def remove_road_station(self) -> None:
        return with_(None,_ttd.script.road.remove_road_station)


    ## land status

    @property
    def has_tree(self) -> bool:
        return _ttd.script.tile.has_tree_on_tile(self)
    @property
    def is_farm(self) -> bool:
        return _ttd.script.tile.is_farm_tile(self)
    @property
    def has_rock(self) -> bool:
        return _ttd.script.tile.is_rock_tile(self)
    @property
    def is_rough(self) -> bool:
        return _ttd.script.tile.is_rough_tile(self)
    @property
    def in_snow(self) -> bool:
        return _ttd.script.tile.is_snow_tile(self)
    @property
    def in_desert(self) -> bool:
        return _ttd.script.tile.is_desert_tile(self)
    @property
    def is_road(self) -> bool:
        return _ttd.script.road.is_road_tile(self)
    @property
    def maybe_road(self) -> bool:
        "The tile either is a road, or we can build one on it"
        return self.is_road or self.is_buildable
    @property
    def is_rail(self) -> bool:
        return _ttd.script.rail.is_rail_tile(self)
    @property
    def count_adjacent_roads(self) -> int:
        return _ttd.script.road.get_neighbour_road_count(self)
    def is_valid_orderflags(self, flags:OrderfFlags) -> bool:
        return _ttd.script.order.are_order_flags_valid(self, flags)

    @property
    def is_tunnel(self) -> bool:
        return _ttd.script.tunnel.is_tunnel_tile(self)
    @property
    def tunnel_dest(self) -> Tile:
        return Tile(_ttd.script.tunnel.get_other_tunnel_end(self))
    @property
    def terrain(self) -> _ttd.script.tile.TerrainType:
        return _ttd.script.tile.get_terrain_type(self)

    def has_road_to(self, other:Tile|Dir):
        """
        This tests a *direct* connection, i.e. the tiles need to be next to each other.
        You can use a direction instead.
        """
        if isinstance(other,Dir):
            if other.x and other.y:
                raise ValueError("You can't have diagonal roads.")
            other = self+other
        return _ttd.script.road.are_road_tiles_connected(self, other._)

    def can_build_road_parts(self, prev: Tile|Dir, next: Tile|Dir):
        if isinstance(prev,Dir):
            prev = tile+prev
        if isinstance(next,Dir):
            next = tile+next
        return _ttd.script.road.can_build_connected_road_parts_here(self, prev, next)

    def Sign(self, text:str) -> Sign:
        return with_(openttd._.Sign, _ttd.script.sign.build_sign, self, openttd.Text(text))

    @property
    def signs(self) -> Signs:
        return openttd._.Signs() @ (lambda s: s.location == self)

    def build_road_to(self, other:Tile|TilePath, full:bool=False, oneway:bool=False):
        # it's rather silly to split that into four, only for
        # script_road.cpp to piece it together again. Oh well. TODO.
        r = _ttd.script.road
        p = (r.build_one_way_road_full if oneway else r.build_road_full) if full else (r.build_one_way_road if oneway else r.build_road)
        if isinstance(other,TilePath):
            other = other.t
        return with_(None,p,self, other)


    ### Bridges ###

    @property
    def has_bridge(self) -> bool:
        return _ttd.script.bridge.is_bridge_tile(self)

    @property
    def bridge(self) -> Bridge:
        if not _ttd.script.bridge.is_bridge_tile(self):
            return None
        return openttd._.Bridge(self, with_(Tile, _ttd.script.bridge.get_other_bridge_end,self))

    # Building: _.BridgeType.build

    def remove_bridge(self) -> None:
        # also available as _.Bridge.remove()
        return with_(None, _ttd.script.bridge.remove_bridge, self)


    ### Tunnels ###

    @property
    def has_tunnel(self) -> bool:
        return _ttd.script.tunnel.is_tunnel_tile(self)

    def build_tunnel(self, roadtype: _ttd.script.vehicle.Type):
        return with_(None,_ttd.script.tunnel.build_tunnel,roadtype, self)

    def build_company_hq(self):
        return with_(None, _ttd.script.company.build_company_hq, self)

    @property
    def slope(self) -> Slope:
        return _ttd.script.tile.get_slope(self)
    @property
    def min_height(self) -> int:
        return _ttd.script.tile.get_min_height(self)
    @property
    def max_height(self) -> int:
        return _ttd.script.tile.get_max_height(self)
    def corner_height(self, corner: _ttd.script.tile.Corner):
        return _ttd.script.tile.get_corner_height(self, corner)
    @property
    def owner(self) -> CompanyID:
        return _ttd.script.tile.get_owner(self)
    def has_transport(self, ttype: _ttd.script.tile.TransportType):
        return _ttd.script.tile.has_transport_type(self, ttype)
    def cargo_acceptance(self, cargo_type: _ttd.script.cargo.Cargo, width: int, height: int, radius: int) -> int:
        return _ttd.script.tile.get_cargo_acceptance(self, cargo_type, width,height,radius)
    def cargo_production(self, cargo_type: _ttd.script.cargo.Cargo, width: int, height: int, radius: int) -> int:
        return _ttd.script.tile.get_cargo_production(self, cargo_type, width,height,radius)

    def raise_(self, slope:Slope) -> None:
        """*sigh* Python syntax"""
        return with_(None, _ttd.script.tile.raise_tile, self, slope)
    def lower(self, slope:Slope) -> None:
        return with_(None, _ttd.script.tile.lower_tile, self, slope)
    def level_to(self, tile: Tile) -> None:
        return with_(None, _ttd.script.tile.level_tiles, self, tile)
    def demolish(self) -> None:
        return with_(None, _ttd.script.tile.demolish_tile, self)
    def plant_tree(self) -> None:
        return with_(None, _ttd.script.tile.plant_tree, self)
    def plant_tree_rect(self, width: int, height: int) -> None:
        return with_(None, _ttd.script.tile.plant_tree_rectangle, self, width, height)

    def is_within_town(self, town: Town):
        """test influence"""
        return _ttd.script.tile.is_within_town_influence(self, town)
    @property
    def authority_town(self) -> Town:
        res = _ttd.script.tile.get_town_authority(self)
        return openttd._.Town(res)
    @property
    def closest_town(self) -> Town:
        return openttd._.Town(_ttd.script.tile.get_closest_town(self))

    @property
    def adjacent(self):
        for d in (Dir.NE,Dir.SE,Dir.SW,Dir.NW):
            try:
                yield self+d
            except ValueError:
                pass

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

    def found_town(self, size:TownSize, city:bool, layout:RoadLayout, name:str):
        return with_(None, _ttd.script.town.found_town, self, site, ciy, layout, openttd.Text(name))


    ## Collections

    def Adjacent(self, diagonal:bool=False) -> Self:
        """Return a set of all tiles next to this one.

        If @diagonal is True, also returns the tiles which share a corner.
        """
        res = Tiles()
        for d in (Dir.NE,Dir.SE,Dir.SW,Dir,SE)+((Dir.N,Dir.E,Dir.S,Dir,W) if diagonal else ()):
            try:
                t = self+d
            except ValueError:
                pass
            else:
                self.add(t)

    @classmethod
    def Rect(self, size:int) -> Self:
        xmin,xmax=max(1,self.x-size),min(self.x+size,_ttd.script.map.get_map_size_x()-1)
        ymin,ymax=max(1,self.y-size),min(self.y+size,_ttd.script.map.get_map_size_y()-1)

        res = self.Tiles()
        for x in range(xmin,xmax+1):
            for y in range(ymin,ymax+1):
                res.add(self+(x,y))
        return res

    @classmethod
    def Diamond(cls, size: int) -> Self:
        xmin,xmax=max(1,self.x-size),min(self.x+size,_ttd.script.map.get_map_size_x()-1)
        ymin,ymax=max(1,self.y-size),min(self.y+size,_ttd.script.map.get_map_size_y()-1)

        res = self.Tiles()
        cx,cy=self.xy
        for x in range(xmin,xmax+1):
            for y in range(ymin,ymax+1):
                if abs(x-cx)+abs(y-cy)>size:
                    continue
                res.add(self+(x,y))
        return res


@define
class TilePath:
    """
    A tile with a path, direction, and a cache for the pathfinder's cost function.

    TODO: rail paths.
    """
    t:Tile=field()
    d:Dir=field()
    _prev:TilePath|None=field(default=None)
    dist:int=field(default=0)
    cache:Any=None
    jump:bool=False # bridge or tunnel

    def __attrs_post_init__(self):
        if self.d is Dir.SAME and self.prev is not None:
            raise ValueError("Can't stand still")
        if not isinstance(self.t, Tile):
            self.t = Tile(self.t)
        if isinstance(self.d,DirJump):
            raise ValueError("Won't create from DirJump. Be explicit.")

    def __getattr__(self,k):
        return getattr(self.t,k)

    @property
    def _(self):
        return self.t

    @property
    def x(self):
        return self.t.x

    @property
    def y(self):
        return self.t.y

    @property
    def xy(self):
        return self.t.xy

    def __hash__(self):
        if self.d is Dir.SAME:
            return hash(self.t)
        return hash(self.t)+self.d.value*(2<<10+2<20)

    def __repr__(self):
        c="" if self.cache is None else "-" if self.cache is False else "+"
        d="_" if self.jump else ""
        return f"Path({self.t} {self.d.name}*{self.dist} {c}{d})"

    def __eq__(self, other:Tile|TilePath):
        """Compares location only!"""
        if self.t.xy != other.xy:
            return False
        if self.d is Dir.SAME:
            return True
        if isinstance(other,(Tile,_ttd.support.Tile_)):
            return self.t == other
        if other.d is Dir.SAME:
            return True
        return self.d is other.d

    def __lt__(self, other:TilePath):
        return self.cache.__lt__(other.cache)

    @overload
    def __add__(self, x:Literal[Turn.S]) -> Self: ...

    @overload
    def __add__(self, x:Turn) -> Self: ...

    def __add__(self, x):
        """Prolong the path."""
        if x is Turn.S:
            # go straight ahead
            if self.jump:
                # after a bridge/tunnel: build a new stretch
                return TilePath(self.t+self.d, self.d, prev=self, dist=1)
            return TilePath(self.t+self.d, self.d, prev=self._prev, dist=self.dist+1)

        if isinstance(x,Turn):
            # No, turn
            if self.d is Dir.SAME:
                raise ValueError("No initial direction, so where to?")
            d=self.d+x
            return TilePath(self.t+d.xy, d, prev=self, dist=1)

        if isinstance(x,(Dir,DirJump)):
            # doesn't move at all?
            if x.n == 0:
                return self
            if self.d is Dir.SAME or x.d in (self.d,Dir.SAME) or self.jump or x.jump:
                # start, turn, or jump
                if self.d is not Dir.SAME and x.d is not Dir.SAME:
                    # can't do a 90° turn on the end of a bridge/tunnel
                    if self.d - x.d not in ({Turn.R,Turn.S,Turn.L} if self.jump else {Turn.RR,Turn.R,Turn.S,Turn.L,Turn.LL}):
                        raise TTDWrongTurn(self.d,x.d, "corner")

                if self.d is Dir.SAME and x.d is Dir.SAME:
                    raise ValueError("can't walk in place")
                return TilePath(self.t+x.xy, self.d if x.d is Dir.SAME else x.d, prev=self, dist=x.n, jump=x.jump)

            # continue on
            return TilePath(self.t+x.xy, self.d, prev=self._prev, dist=self.dist+x.n)

        return NotImplemented

    def __mod__(self, other):
        return self.t.__mod__(other)

    @property
    def next(self):
        """Return the next tile the current path would lead to."""
        return self.t+self.d

    @property
    def prev(self):
        """Return the adjacent previous tile.
        Note: the previous tile computed when it's not a corner,
        so cache data might be lost."""
        if self.dist>1:
            return TilePath(self.t-self.d,self.d, prev=self._prev, dist=self.dist-1)
        return self._prev

    @property
    def start(self):
        """Return the start tile of this leg.
        """
        return self.t-self.d*self.dist

    @property
    def prev_turn(self):
        return self._prev

    @property
    def reversed(self):
        this = self
        last = None
        if this.d is not Dir.SAME:
            # build an explicit start tile
            last = TilePath(self.t,Dir.SAME)
            yield last
        while this is not None:
            if this.d is not Dir.SAME:  # skip no-movement tiles
                d=this.d.back
                last = TilePath(this.t+d*this.dist, d, prev=last, dist=this.dist, jump=this.jump)
                yield last
            this=this._prev

    def __iter__(self):
        """Iterate the path, starting at the beginning."""
        if self._prev is not None:
            yield from self._prev
        yield self

    def show(self):
        res = self.prev_turn.show() if self.prev_turn is not None else ""
        if self.d is Dir.SAME:
            res += _places[self.jump]
        else:
            i = self.d.value + (8 if self.jump else 0)
            res += _arrows[i]*max(self.dist,1)
        return res



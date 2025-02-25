#
"""
This is a straight translation of Convoy, v.11, by GeekToo.
"""

from __future__ import annotations

import openttd
from openttd.base import AIScript
from openttd.lib.pathfinder.road import RoadPath
import operator
from openttd.util import testmode_if, PlusSet
from openttd._main import exceptions,estimating,test_mode
from itertools import pairwise
from functools import partial
import openttd.cargo
import openttd.order
import openttd.road
import openttd.station
import openttd.vehicle
from attrs import define,field
from collections import defaultdict

Date = openttd._.Date
Dir = openttd._.Dir
Tile = openttd._.Tile
TilePath = openttd._.TilePath
Tiles = openttd._.Tiles
Depots = openttd._.Depots
Towns = openttd._.Towns
Stations = openttd._.Stations
StationType = openttd.station.Type
Vehicle = openttd._.Vehicle
TTDError = openttd._.TTDError

Slope = openttd.tile.Slope
Err = openttd.error.Error
VT_Road = openttd.vehicle.Type.ROAD
RT_Road = openttd.road.Type.ROAD
TT_Road = openttd._.TransportType.ROAD
OrderFlags = openttd.order.Flags

attr_ = operator.attrgetter

# Comments that start with '#=' describe Convoy equivalents

#= Tile: see openttd.tile.Tile
#= Tile::GetAdjacentTiles(tile): tile.adjacent
#= Tile::IsRoadBuildable(tile): tile.maybe_road


class Script(AIScript):
    #= Pathfinder: integrated here
    #= TownManager: integrated here
    """
    Main class for our Convoy clone.
    """
    ATTRS = (
        ("agressive",False),
        ("d_min",70),
        ("d_max",140),
    )

    lines:dict[frozenset[Station],Line]
    depots:dict[Town,Tile]
    stations:dict[Town,PlusSet[Station]]

    retry_towns:int = 0
    # skip trying to find a new pair of towns if we didn't get one often
    # enough, as to conserve CPU
    date_town_acc_update = 0

    def __init__(self, *a, **kw):
        super().__init__(*a,**kw)

        self.selling: PlusSet[Vehicle] = PlusSet()
        self.lines = dict()
        self.depots = defaultdict(PlusSet)  # depots per town
        self.stations = defaultdict(PlusSet)  # stations per town

    #= Pathfinder.build_road
    def build_road(self, start:list[Tile]|Tile, target:list[Tile]|Tile):
        retry_find = True
        plan_retries = 0
        avoid = set()

        def err(step:TilePath, err:TTDError):
            if step.jump:
                raise err
            if step.dist == 1:
                raise err
            # TODO return True for retrying, e.g. if a vehicle is in the way
            return None

        while retry_find:
            retry_find = False
            if isinstance(start,Tile):
                start=(start,)
            if isinstance(target,Tile):
                target=(target,)

            pathfinder = RoadPath(start,target)
            pathfinder.cost_slope = 50

            path = pathfinder.run()
            if path is None:
                for t in start[0].t.Rect(2):
                    t.Sign(t.content_str)
                return

            while True:
                try:
                    path.build_road(on_error=err)
                except TTDError as exc:
                    # TODO classify as to the list below
                    # and decide whether to retry
                    self.log.exception("Build Fail: %r", exc)
                    t = getattr(exc,"tile", None)
                    if tile is not None:
                        avoid.add(tile)
                        break
                    else:
                        return False  # could not build road, decide what to do

                return sum(p.dist for p in path)

#                                match err:
#                                    case e.misc.NONE | e.misc.ALREADY_BUILT:
#                                        if build_retries:
#                                            build_retries -= 1
#                                    case e.misc.PRECONDITION_FAILED | e.newgrf.SUPPLIED_ERROR | e.misc.NOT_ENOUGH_CASH | e.local.AUTHORITY_REFUSES:
#                                        self.log.info(f"Build road failed(fatal) {err} {parnt.xy} {path.xy} {path.slope}")
#                                        return False
#                                    case e.vehicle.IN_THE_WAY:
#                                        self.log.info(f"Build road failed (retry) {err} {parnt.xy} {path.xy}")
#                                        self.sleep(0.5)
#                                        retry_build=True
#                                    case e.area.NOT_CLEAR:
#                                        self.log.info(f"Build road failed (demolish + retry) {err} {parnt.xy} {path.xy}")
#                                        path.demolish()
#                                        retry_build = False
#                                        retry_find = True
#                                    case e.owned.BY_ANOTHER_COMPANY | e.FLAT_LAND_REQUIRED | Err.LAND_SLOPED_WRONG | Err.SITE_UNSUITABLE | Err.TOO_CLOSE_TO_EDGE:
#                                        self.log.info(f"Build road failed (replan) {err} {parnt.xy} {path.xy}")
#                                        retry_build = False
#                                        retry_find = True
#                                    case _:
#                                        self.log.info(f"Build road failed (unknown) {err} {parnt.xy} {path.xy}")
#                                        retry_find = True
#

    #= TownManager::CreateExitRoute
    def create_exit_route(self, busstop:Tile, town:Town, size:int=5):
        exits = busstop.Rect(size)
        exits @= attr_("is_road")
        exits @= lambda t: t.slope == Slope.FLAT
        center = town.center
        exits = list(exits.max_n(2, lambda t: t.d_manhattan(center)))
        with self.test_mode():
            if not RoadPath((TilePath(center,Dir.SAME),),exits).run():
                self.log.warn(f"No way for stop at {busstop.xy} to reach {exit.xy} ??")
        return exit


    #= TownManager::FindLineBusStopLocation
    def find_bus_stop_location(self, town:Town, cargo: int, estimate:bool, size:int=8) -> Tile|None:
        """
        Find a good place for a bus stop.
        """
        tile = town.center
        tl = tile.Rect(size)

        # remove all tiles that are already covered by a station
        for tile in tl @ (lambda t:t.is_station):
            tl -= tile.Rect(4 if tile.owner == self.company else 1)
            # This keeps our own stations a bit apart,
            # but we are not so modest with other players' stations ...

        if not tl:
            # We already have perfect coverage
            return None

        # limit the list to non-sloped buildable tiles that are next to a road tile.
        tl @= lambda t: not t.is_road and t.slope is Slope.FLAT and t.count_adjacent_roads > 0

        if not tl:
            self.log.info(f"Find busstop location in {town}, no suitable tiles!")
            return None

        radius = StationType.BUS_STOP.coverage

        for tile in tl:
            val = tile.cargo_acceptance(cargo, 1,1, radius)
            if val >= 15:
                with testmode_if(not estimate):
                    with exceptions(False):
                        if not tile.is_buildable and not tile.demolish():
                                continue
                # Found a candidate.
                # tile.Sign(f"ex {val}")
                return tile

        self.log.info("Find busstop location, in %s, acceptance too low", town.name)
        return None


    #= TownManager::BuildBusStop
    def build_bus_stop(self, tile):
        """
        Build a (non-drive-thru) bus stop here.
        """
        for tile2 in tile.adjacent:
            if not tile2.is_road:
                continue
            for _ in range(10):
                try:
                    tile2.build_road_to(tile)
                except TTDError as exc:
                    self.log.error("TryBuild %s: Error %r",tile,exc)
                    if exc.err == openttd.str.error.ALREADY_BUILT:
                        break
                    if exc.err == openttd.str.error.BUILDING_MUST_BE_DEMOLISHED:
                        tile.demolish()
                        continue
                    if exc.err == openttd.str.error.ROAD_VEHICLE_IN_THE_WAY:
                        self.sleep(10)
                        continue

                    raise
                else:
                    break
            else:
                # self.log.info("Build busstop problem")
                continue  # try the next tile

            tile.build_road_station(tile2, openttd._.RoadVehicleType.BUS)
            self.log.debug("New station @ %s in %s",tile,tile.closest_town.name)
            return True

        self.log.error("TryBuild: unsuccessful @ %s",tile)
        return False

    #= TownManager::EstimateAcceptance
    def estimate_acceptance(self, town:Town):
        loc = self.find_bus_stop_location(town, self.passenger_cargo, True)
        if not loc:
            return 0
        return town.center.cargo_acceptance(self.passenger_cargo,1,1, StationType.BUS_STOP.coverage)


    #= RoutePlanner::FindUnusedTowns
    def find_unused_town(self):

        self.log.info("Find a town");
        for town in Towns().sorted_max(lambda t: t.population):
            self.log.info(f"Acceptance of {town}:{town.name}: {self.estimate_acceptance(town)}");
            area = town.center.Rect(8)
            if not self.agressive:
                area @= lambda t:t.is_road_station
            if not area:
                break
        else:
            self.log.info("No unused town!");
            return

        self.log.info("Find second town");

        dm = town.center.d_manhattan
        for town2 in (Towns() @ (lambda t: self.d_min <= dm(t.center) <= self.d_max)).sorted_max(lambda t: t.population):
            self.log.info(f"Acceptance of {town2}:{town2.name}: {self.estimate_acceptance(town2)}");
            area = town2.center.Rect(8)
            if not self.agressive:
                area @= lambda t:t.is_road_station
            if not area:
                break
        else:
            self.log.info("No unused second town!");
            return

        # TODO maybe find a third town
        return (town,town2)


    def has_money(self, amount:int) -> bool:
        """Do I have that much money?

        If not, try to get it.
        """
        bal = self.company.bank_balance
        if bal > amount:
            return True

        return (self.company.bank_balance +
                self.company.max_loan_amount -
                self.company.loan_amount > amount)


    def main(self):
        self.set_name()
        openttd._.RoadType.ROAD.set_current()
        self.log.info(f"{self.name} starting in {'agressive' if self.agressive else 'lenient'} mode")

        cargoes = openttd._.Cargo.List()
        cargoes @= lambda c: c.has_class(openttd.cargo.Class.PASSENGERS)
        if not cargoes:
            # There is no passenger cargo, so adding buses is useless.
            self.log.warning("There are no passengers in this game. Exiting.")
            return
        if len(cargoes) > 1:
            # Find the largest city and ask which type of passengers it accepts most of.
            city = Towns().max(lambda t:t.population)
            self.passenger_cargo = cargoes.max(lambda c: city.location.cargo_acceptance(c,1,1,5))
        else:
            self.passenger_cargo = cargoes.any
    #
        engines = openttd._.Engines(VT_Road)
        engines @= lambda e: e.road_type == RT_Road
        engines @= lambda e: e.cargo == self.passenger_cargo

        if not engines:
            self.log.error("Stopping because no road passenger vehicles are available");
            return

        # For restarting the script, collect current data
        for t in Depots(TT_Road):
            self.depots[t.closest_town].add(t)
        for s in Stations(StationType.BUS_STOP):
            self.stations[s.closest_town].add(s)

            for v in s.vehicles:
                towns = frozenset(st.closest_town for st in v.stations)
                try:
                    l=self.lines[towns]
                except KeyError:
                    self.lines[towns]=l=Line(towns)
                l.cars.add(v)
                l.stations[s.closest_town].add(s)

        for l in self.lines.values():
            l.restored()

        i=0
        while True:
            self.test_stop()
            self.sleep(.1)

            if i%200 == 1:
                self.manage_loan()
                self.manage_vehicles()

            if i%50 == 1:
                self.add_vehicles()
                self.manage_building()

            i += 1

    def manage_building(self):
        self.company.set_loan_amount(self.company.max_loan_amount)

        for towns,line in self.lines.items():
            if not self.has_money(25000):
                return

            line.build()

        if self.retry_towns > 20:
            return

        towns = self.find_unused_town()
        if not towns:
            self.retry_towns += 1
        else:
            t = frozenset(towns)
            assert t not in self.lines
            self.lines[t] = line = Line(self, towns)
            line.build()
        self.manage_loan()


    #= Line::AddDepot(tile)
    def add_depot(self, station:Station, town: Town) -> bool:
        """
        Add a depot close to @tile, in the direction of @town.
        """
        front = station.location.road_station_front
        tiles = front.Rect(10)
        tiles @= lambda t: t.count_adjacent_roads > 0
        tiles @= lambda t: not t.is_road
        tiles @= lambda t: t.slope == Slope.FLAT
        # XXX this code (adapted from the original) can find an unreachable
        # location (which is why this version adds a pathfind below).
        # Better solution: follow the actual road and build a depot as soon
        # as there is a suitable spot.

        def err(step:TilePath, exc:TTDError):
            if exc.err == openttd.str.error.ALREADY_BUILT:
                return False
            raise exc

        def try_this(tile):
            for adj in tile.adjacent:
                if not adj.is_road or adj.slope != Slope.FLAT:
                    continue
                if not tile.is_buildable:
                    try:
                        tile.demolish()
                    except TTDError as exc:
                        self.log.info("Tried to clean {adj.xy} but got {exc}")
                        continue

                pathfinder = RoadPath((TilePath(adj,Dir.SAME),),(TilePath(front,Dir.SAME),))
                path = pathfinder.run()
                if not path:
                    continue

                for _ in range(10):
                    try:
                        tile.build_road_depot(adj)
                        path.build_road(on_error=err)
                    except TTDError as exc:
                        self.log.info("Tried to build at {tile.xy} but got {exc}")
                        self.sleep(1)
                    else:
                        return True

            self.log.info("Failed to build at {tile.xy}")
            return False

        loc = town.center
        for tile in tiles.sorted_min(lambda t: t.d_manhattan(loc)):
            if try_this(tile):
                self.depots[tile.closest_town].add(tile)
                return True
        else:
            self.log.info("Failed to build a depot for {station.xy}")
            return False


    def set_name(self):
        name="Convoy"
        if self.company.set_name(name):
            self.name=name
            return
        i = 2
        while i<30:
            name = f"Convoy#{i}"
            if self.company.set_name(name):
                self.name=name
                return
            i += 1
        raise RuntimeError("Cannot set company name: ??")

    def manage_loan(self, min_balance=None):
        interval = self.company.loan_interval
        if min_balance is None:
            # keep 2*interval in the bank by default
            min_balance=2*interval
        balance = self.company.bank_balance - min_balance
        loan = self.company.loan_amount
        if balance > 0:
            if loan == 0:
                return True
            if loan < balance:
                self.company.set_loan_amount(0)
                return True

        # round up to the next interval
        loan = loan-balance + interval-1
        loan -= loan%interval
        with exceptions(False):
            return self.company.set_loan_amount(loan)

    def manage_vehicles(self):
        for line in self.lines.values():
            if line.try_rebuild:
                continue
            line.manage_vehicles()

    def add_vehicles(self):
        for line in self.lines.values():
            if line.try_rebuild:
                continue
            line.add_vehicles()



@define(init=False)
class Line:
    script:Script=field()

    pending:int=0
    date_last:int=0
    vehicles:PlusSet[Vehicle] = field(factory=PlusSet)
    stations:dict[Town,Station] = field(factory=dict)
    date_last_vehicle:int = field(default=0)
    n_buses:int|None=field(default=None)
    try_rebuild:bool = field(default=True)
    start_station = field(default=0)
    to_sell: PlusSet[Vehicle] = field(factory=PlusSet)
    failed:bool=field(default=False)

    def __init__(self, script, towns:list[Town]):
        self.__attrs_init__(script)

        for town in towns:
            self.stations[town] = None

    def build(self):
        if self.failed:
            return
        if not self.try_rebuild:
            return
        if not self.build_stations():
            return
        if not self.build_road():
            return
        if not self.build_depots():
            return
        if not self.add_vehicles():
            return
        self.try_rebuild = False

    def restored(self):
        pass

    def build_road(self):
        sn = list(self.stations.values())
        if len(sn) > 2:
            ts.append(sn[0])
        for sn1,sn2 in pairwise(sn):
            # TODO use Station.tiles_for
            sp1 = sn1.location.road_station_front
            sp2 = sn2.location.road_station_front
            self.script.build_road((TilePath(sp1,Dir.SAME),),(TilePath(sp2,Dir.SAME),))
        return True

    def build_stations(self) -> bool:
        """
        Build new stations. Returns False if no open locations were found.
        """
        for town,station in self.stations.items():
            if station is not None:
                continue

            loc = self.script.find_bus_stop_location(town, self.script.passenger_cargo, False)
            if loc is None:
                return False
            if not self.script.build_bus_stop(loc):
                return False
            self.stations[town]=loc.station

        ts = list(self.stations.items())
        if len(ts) > 2:
            ts.append(ts[0])
        for a,b in pairwise(ts):
            self.script.create_exit_route(a[1].location.road_station_front, b[0])

        # if we got here we have built (or found) a station in every town
        return True


    #= Line::CreateNewLine
    def build_depots(self) -> None:
        """
        Build depots in each town, towards the next town
        """
        depots:list[tuple[Town,Station]] = list(self.stations.items())
        depots.append(depots[0])  # for going back to the start

        for d1,d2 in pairwise(depots):
            if d1[0] not in self.script.depots:
                self.script.add_depot(d1[1], d2[0])
        return True

    #= Line::AddVehicles
    def add_vehicles(self):
        """
        Add vehicles.
        """
        # how many?
        if self.n_buses is None:
            self.n_buses = self.estimate_buses_needed()

        if self.n_buses <= len(self.vehicles):
            return

        # Not too fast please.
        if Date.now() - self.date_last_vehicle <= 10:
            return

        # OK so we do need some. Figure out what to buy. Capacity is
        # important, but we need to be able to afford it.

        engine_list = openttd._.Engines(VT_Road)
        engine_list @= lambda e: (e.road_type == RT_Road and e.cargo == self.script.passenger_cargo)

        balance = self.script.company.bank_balance
        engine_list @= lambda e: e.price < balance
        if not engine_list:
            # not enough money. probably.
            return False

        bus_model = engine_list.max(lambda e: e.capacity)

        def one_depot():
            for town in self.stations.keys():
                for depot in self.script.depots[town]:
                    return depot
            raise ValueError("No depots! {','.join(t.name for t in self.stations.keys())}")

        depot = one_depot()
        v = Vehicle.New(depot, bus_model)
        try:
            vo = v.orders
            for t,s in self.stations.items():
                depots = self.script.depots[t]
                if depots:
                    vo.append(depots.any, OrderFlags.SERVICE_IF_NEEDED)
                vo.append(s.location)  # TODO find an actual tile
            try:
                vo[self.start_station*2+1].goto()
            except TTDError:
                pass
            v.start()
        except Exception as exc:
            # If anything went wrong, toss the thing.
            self.script.log.exception("Problem with vehicle: %r", exc)
            v.sell()
        else:
            self.vehicles.add(v)
            self.start_station = (self.start_station+1) % len(self.stations)
            self.date_last_vehicle = Date.now()

        return True


    #= Line::EstimateBusesNeeded
    def estimate_buses_needed(self):
        if len(self.stations) < 2:
            return 0
        radius = StationType.BUS_STOP.coverage
        acceptance = sum(s.location.cargo_acceptance(self.script.passenger_cargo,1,1,radius)
                   for s in self.stations.values())
        locs = [s.location for s in self.stations.values()]
        locs.append(locs[0])
        distance = sum(t1.d_manhattan(t2) for t1,t2 in pairwise(locs))

        n_buses = int(2 + (acceptance / 35) * (distance / 70) + 0.7)
        # the original code has distance/35, but with two stations we count the way twice

        return min(n_buses, 25)

    def manage_vehicles(self):
        cars = PlusSet(self.vehicles)
        cars @= lambda v:v.age>700
        cars @= lambda v:v.profit_last_year < -100
        cars @= lambda v:v not in self.to_sell

        # Find unprofitable cars and order them to the nearest depot.
        if cars and all(s.rating_for(self.script.passenger_cargo) > 40 for s in self.stations.values()):
            for c in cars:
                c.send_to_depot()
                self.to_sell.add(c)

        # … then sell the cars as soon as they're in a depot.
        sold = set()
        for c in self.to_sell:
            if c.stopped_in_depot:
                c.sell()
                sold.add(c)
        self.to_sell -= sold

        if not self.script.has_money(12000):
            return

        # Check if we need more buses than estimated:
        # * less than 35 buses on the road
        # * the previous add-on bus was bought more than 50 days ago
        # * more than 45 people waiting (total) and at least one town rating worse than 75%
        # * (add) … or more than 200 people waiting
        #
        if len(self.vehicles) >= 35:
            return
        if Date.now() - self.date_last_vehicle <= 50:
            return
        waiting = sum(s.cargo_waiting(self.script.passenger_cargo) for s in self.stations.values())
        if waiting <= 45:
            return
        elif waiting <= 200 and all(s.rating_for(self.script.passenger_cargo) >= 75 for s in self.stations.values()):
            return

        try:
            # Pick a vehicle and a depot
            v = None
            vo = self.vehicles.any
            for t,s in self.stations.items():
                if (dep := self.script.depots[t].any) is not None:
                    v = vo.clone(dep, True)
                    v.start()
                    break
            # TODO jump the order list to the station in the town where the depot is
        except Exception as exc:
            self.script.log.exception("Problem with vehicle: %r", exc)
            if v is not None:
                v.sell()
        else:
            self.vehicles.add(v)
            self.start_station = (self.start_station+1) % len(self.stations)
            self.date_last_vehicle = Date.now()


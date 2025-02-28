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
TTDCommandError = openttd._.TTDCommandError

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
        ("network",0),
        ("d_min",70),
        ("d_max",140),
        ("waiting",10),
    )

    lines:dict[frozenset[Station],Line]
    depots:dict[Town,Tile]
    stations:dict[Town,PlusSet[Station]]

    agressive:bool
    network:int
    waiting:int
    d_min:int
    d_max:int

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

            for _ in range(30):
                try:
                    path.build_road(on_error=err)
                except TTDCommandError as exc:
                    if exc.err == openttd.str.error.ROAD_VEHICLE_IN_THE_WAY:
                        self.sleep(10)
                        continue
                    if exc.err == openttd.str.error.NOT_ENOUGH_CASH_REQUIRES_CURRENCY:
                        if not self.manage_loan(10000):
                            break
                        continue

                    # TODO classify as to the list below
                    # and decide whether to retry
                    self.log.exception("Build Fail: %r", exc)
                    t = getattr(exc,"tile", None)
                    if t is not None:
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
    def create_exit_route(self, busstop:Tile, town:Town, size:int=5) -> bool:
        exits = busstop.Rect(size)
        exits @= attr_("is_road")
        exits @= lambda t: t.slope == Slope.FLAT
        center = town.center
        exits = list(exits.max_n(2, lambda t: t.d_manhattan(center)))
        if not exits:
            return False

        with self.test_mode():
            if not RoadPath((TilePath(center,Dir.SAME),),exits).run():
                self.log.warn(f"No way for stop at {busstop.xy} to reach {exit.xy} ??")
                return False
        return True


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
            if town in self.stations and not self.network:
                continue
            if not self.estimate_acceptance(town):
                continue
            if not self.agressive:
                area = town.center.Rect(8)
                # can't be ours because we already checked that the town
                # doesn't have one of our stations
                area @= lambda t:(t.is_road_station and t.owner != self.company)
                if area:
                    continue

            self.log.info("Find second town for {town.name}");

            dm = town.center.d_manhattan
            for town2 in (Towns() @ (lambda t: self.d_min <= dm(t.center) <= self.d_max)).sorted_max(lambda t: t.population):
                if town2 in self.stations and self.network < 2:
                    continue
                if not self.estimate_acceptance(town2):
                    continue
                if not self.agressive:
                    area = town2.center.Rect(8)
                    # … thus not skipping our own stations here either
                    area @= lambda t:(t.is_road_station and t.owner != self.company)
                    if area:
                        continue

                # TODO maybe find a third town

                tt = frozenset((town,town2))
                if tt not in self.lines:
                    return tt

        else:
            self.log.info("No unused towns!");
            return

    def has_money(self, amount:int) -> bool:
        """Do I have that much money?

        If not, try to get it.
        """
        bal = self.company.bank_balance
        if bal > amount:
            return True

        self.manage_loan(amount)


    def main(self):
        self.set_name()
        openttd._.RoadType.ROAD.set_current()
        self.log.info(f"{self.company.name} starting in {'agressive' if self.agressive else 'lenient'} mode")

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
                    self.lines[towns]=l=Line(self,towns)
                l.vehicles.add(v)
                l.stations[s.closest_town] = s

        for l in self.lines.values():
            l.restored()

        i=0
        n_towns = len(openttd._.Towns())
        n_towns = 4*n_towns**1.5
        while True:
            self.test_stop()
            self.sleep(.1)

            if i%200 == 1:
                self.manage_loan(repay=True)
                self.manage_vehicles()

            if i%n_towns == 1:
                self.add_vehicles()
                self.manage_building()

            i += 1

    def manage_building(self):
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
        tiles @= lambda t: (not t.is_road and not t.is_road_station and not t.is_road_depot)
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
        if self.company.name == name:
            return
        with exceptions(False):
            if self.company.set_name(name):
                return
            i = 2
            while i<30:
                name = f"Convoy#{i}"
                if self.company.name == name:
                    return
                if self.company.set_name(name):
                    return
                i += 1
            raise RuntimeError("Cannot set company name: ??")

    def manage_loan(self, min_balance=None, repay=False):
        interval = self.company.loan_interval
        balance = self.company.bank_balance
        if min_balance is None:
            # keep 2*interval in the bank by default, but add some hysteresis
            if balance < interval*2:
                min_balance = 2*interval
            elif balance > 4*interval:
                min_balance = 3*interval
            else:
                return True
        balance -= min_balance
        loan = self.company.loan_amount
        if balance > 0:
            if loan == 0:
                return True
            if loan < balance:
                if repay:
                    self.company.set_loan_amount(0)
                return True

        # round to the next interval
        current_loan = loan
        loan = loan-balance + interval-1
        loan -= loan%interval
        with exceptions(False):
            if current_loan > loan and not repay:
                return True
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
        try:
            sn = list(self.stations.values())
            if len(sn) > 2:
                ts.append(sn[0])
            for sn1,sn2 in pairwise(sn):
                # TODO use Station.tiles_for
                sp1 = sn1.location.road_station_front
                sp2 = sn2.location.road_station_front
                self.script.build_road((TilePath(sp1,Dir.SAME),),(TilePath(sp2,Dir.SAME),))
            return True
        except TTDCommandError:
            self.failed=True
            return False

    def build_stations(self) -> bool:
        """
        Build new stations. Returns False if no open locations were found.
        """
        for town,station in self.stations.items():
            if station is not None:
                continue
            if (sn := self.script.stations[town]):
                station = sn.any
                self.stations[town] = station

            else:
                loc = self.script.find_bus_stop_location(town, self.script.passenger_cargo, False)
                if loc is None:
                    self.failed = True
                    return False
                if not self.script.build_bus_stop(loc):
                    return False
                self.stations[town]=loc.station
                sn.add(loc.station)

        ts = list(self.stations.items())
        if len(ts) > 2:
            ts.append(ts[0])
        for a,b in pairwise(ts):
            with exceptions(False):
                self.script.create_exit_route(a[1].location.road_station_front, b[0])
                # On error:
                # Most likely the station's general location doesn't match
                # the actual station. This happens when the user extends the
                # station. TODO find the station's actual bus station tiles.

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

        # Figure out how many are blocked, so we don't add to an existing
        # gridlock
        blocks = self.vehicles @ (lambda v: not v.tile.is_station and not v.tile.is_road_depot)
        blocks @= lambda v: (v.speed == 0 and not v.is_broken)
        if len(blocks) > len(self.vehicles) * self.script.waiting/100:
            # TODO if they're all waiting on the same station, we
            # should think about extending it
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
            with exceptions(False):
                vo[self.start_station*2+1].goto()
                # Happens when one of the locations couldn't get a depot
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
        # Find unprofitable cars
        cars = PlusSet(self.vehicles) - self.to_sell
        cars @= lambda v:v.age>700
        cars @= lambda v:v.profit_last_year < -100

        # … and order them to the nearest depot
        if cars and all(s.rating_for(self.script.passenger_cargo) > 40 for s in self.stations.values()):
            for c in cars:
                c.send_to_depot()
                self.to_sell.add(c)

        # … then sell the cars as soon as they're in it.
        sold = set()
        for c in self.to_sell:
            if c.stopped_in_depot:
                c.sell()
                sold.add(c)
                self.vehicles.remove(c)
        self.to_sell -= sold

        # Check if we need more buses than estimated.
        # * less than 35 buses on the road
        #   (20 when networking)
        # * the last add-on bus was bought more than 50 days ago
        # * we have enough money
        # * more than 45 people waiting
        # * at least one town rating worse than 75% (70% when networking is on)
        #   * or more than 200 people waiting
        #
        if self.n_buses > len(self.vehicles):
            return  # managed by add_vehicles
        if len(self.vehicles) >= (20 if self.script.network else 35):
            return
        if Date.now() - self.date_last_vehicle <= 50:
            return
        while True:
            vo = self.vehicles.any
            try:
                if not self.script.has_money(vo.engine_type.price * 3/2):
                    return
            except TTDCommandError:
                # somebody sold this bus (or maybe it crashed).
                self.vehicles.remove(vo)
            except StopIteration:
                # somebody sold all our buses?!?
                return
            else:
                break

        waiting = 0
        for s in self.stations.values():
            for sn in self.stations.values():
                if s == sn:
                    continue
                waiting += s.cargo_waiting_via(sn,self.script.passenger_cargo)

        if waiting <= 45:
            return
        elif waiting <= 200 and all(s.rating_for(self.script.passenger_cargo) >= (70 if self.script.network else 75) for s in self.stations.values()):
            return

        try:
            # Pick a vehicle and a depot
            v = None
            for t,s in self.stations.items():
                if (dep := self.script.depots[t].any) is not None:
                    v = vo.clone(dep, True)
                    with exceptions(False):
                        v.orders[self.start_station*2+1].goto()
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


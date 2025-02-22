from math import sqrt

import numpy as np
from numpy.testing import (
    assert_,
    assert_allclose,
    assert_equal,
    assert_raises,
    assert_warns,
)
from pytest import mark

from pyvrp.constants import MAX_VALUE
from pyvrp.exceptions import ScalingWarning
from tests.helpers import read


@mark.parametrize(
    ("where", "exception"),
    [
        ("data/UnknownEdgeWeightFmt.txt", ValueError),
        ("data/UnknownEdgeWeightType.txt", ValueError),
        ("somewhere that does not exist", FileNotFoundError),
        ("data/FileWithUnknownSection.txt", ValueError),
        ("data/DepotNotOne.txt", ValueError),
        ("data/DepotsNotLowerIndices.txt", ValueError),
        ("data/TimeWindowOpenLargerThanClose.txt", ValueError),
        ("data/EdgeWeightsNoExplicit.txt", ValueError),
        ("data/EdgeWeightsNotFullMatrix.txt", ValueError),
    ],
)
def test_raises_invalid_file(where: str, exception: Exception):
    """
    Tests that ``read()`` raises when there are issues with the given file.
    """
    with assert_raises(exception):
        read(where)


def test_raises_unknown_round_func():
    """
    Tests that ``read()`` raises when the rounding function is not known.
    """
    with assert_raises(TypeError):
        # Unknown round_func, so should raise.
        read("data/OkSmall.txt", round_func="asdbsadfas")

    # Is the default round_func, so should not raise.
    read("data/OkSmall.txt", round_func="none")


def test_reading_OkSmall_instance():
    """
    Tests that the parsed data from the "OkSmall" instance is correct.
    """
    data = read("data/OkSmall.txt")

    # From the DIMENSION, VEHICLES, and CAPACITY fields in the file.
    assert_equal(data.num_clients, 4)
    assert_equal(data.num_vehicles, 3)
    assert_equal(data.num_vehicle_types, 1)
    assert_allclose(data.vehicle_type(0).capacity, 10)

    # From the NODE_COORD_SECTION in the file
    expected = [
        (2334, 726),
        (226, 1297),
        (590, 530),
        (435, 718),
        (1191, 639),
    ]

    for loc in range(data.num_locations):
        assert_allclose(data.location(loc).x, expected[loc][0])
        assert_allclose(data.location(loc).y, expected[loc][1])

    # From the EDGE_WEIGHT_SECTION in the file
    expected = [
        [0, 1544, 1944, 1931, 1476],
        [1726, 0, 1992, 1427, 1593],
        [1965, 1975, 0, 621, 1090],
        [2063, 1433, 647, 0, 818],
        [1475, 1594, 1090, 828, 0],
    ]

    # For instances read through VRPLIB/read(), distance is duration. So the
    # dist/durs should be the same as the expected edge weights above.
    for frm in range(data.num_locations):
        for to in range(data.num_locations):
            assert_allclose(data.dist(frm, to), expected[frm][to])
            assert_allclose(data.duration(frm, to), expected[frm][to])

    # From the DEMAND_SECTION in the file
    expected = [0, 5, 5, 3, 5]

    for loc in range(1, data.num_locations):  # excl. depot (has no delivery)
        assert_allclose(data.location(loc).delivery, expected[loc])

    # From the TIME_WINDOW_SECTION in the file
    expected = [
        (0, 45000),
        (15600, 22500),
        (12000, 19500),
        (8400, 15300),
        (12000, 19500),
    ]

    for loc in range(data.num_locations):
        assert_allclose(data.location(loc).tw_early, expected[loc][0])
        assert_allclose(data.location(loc).tw_late, expected[loc][1])

    # From the SERVICE_TIME_SECTION in the file
    expected = [0, 360, 360, 420, 360]

    for loc in range(1, data.num_locations):  # excl. depot (has no service)
        assert_allclose(data.location(loc).service_duration, expected[loc])


def test_reading_En22k4_instance():  # instance from CVRPLIB
    """
    Tests that the small E-n22-k4 instance from CVRPLIB is correctly parsed.
    """
    data = read("data/E-n22-k4.txt", round_func="trunc1")

    assert_equal(data.num_clients, 21)
    assert_equal(data.num_depots, 1)
    assert_equal(data.num_locations, 22)
    assert_allclose(data.vehicle_type(0).capacity, 60_000)

    assert_equal(len(data.depots()), data.num_depots)
    assert_equal(len(data.clients()), data.num_clients)
    assert_equal(data.num_locations, data.num_depots + data.num_clients)

    # Coordinates are scaled by 10 to align with 1 decimal distance precision
    assert_allclose(data.location(0).x, 1450)  # depot [x, y] location
    assert_allclose(data.location(0).y, 2150)

    assert_allclose(data.location(1).x, 1510)  # first customer [x, y] location
    assert_allclose(data.location(1).y, 2640)

    # The data file specifies distances as 2D Euclidean. We take that and
    # should compute integer equivalents with up to one decimal precision.
    # For depot -> first customer:
    # For depot -> first customer:
    #      dX = 151 - 145 = 6
    #      dY = 264 - 215 = 49
    #      dist = sqrt(dX^2 + dY^2) = 49.37
    #      int(10 * dist) = 493
    assert_allclose(data.dist(0, 1), 493)
    assert_allclose(data.dist(1, 0), 493)

    # This is a CVRP instance, so all other fields should have default values.
    for loc in range(1, data.num_locations):
        assert_allclose(data.location(loc).service_duration, 0)
        assert_allclose(data.location(loc).tw_early, 0)
        assert_allclose(data.location(loc).tw_late, np.iinfo(np.int64).max)
        assert_allclose(data.location(loc).release_time, 0)
        assert_allclose(data.location(loc).prize, 0)
        assert_equal(data.location(loc).required, True)


def test_reading_RC208_instance():  # Solomon style instance
    """
    Tests that a Solomon-style VRPTW instance is correctly parsed.
    """
    data = read(
        "data/RC208.txt", instance_format="solomon", round_func="trunc1"
    )

    assert_equal(data.num_clients, 100)
    assert_equal(data.num_depots, 1)
    assert_equal(data.num_locations, 101)

    assert_equal(data.num_vehicles, 25)
    assert_equal(data.num_vehicle_types, 1)

    vehicle_type = data.vehicle_type(0)
    expected_name = ",".join(str(idx + 1) for idx in range(data.num_vehicles))

    assert_equal(vehicle_type.num_available, 25)
    assert_equal(vehicle_type.name, expected_name)

    # The trunc1 rounding function ensures everything is scaled by 10 and
    # truncated to integers (for 1 decimal integer precision).
    assert_allclose(vehicle_type.capacity, 10_000)

    assert_allclose(data.location(0).x, 400)  # depot [x, y] location
    assert_allclose(data.location(0).y, 500)
    assert_allclose(data.location(0).tw_early, 0)
    assert_allclose(data.location(0).tw_late, 9600)

    assert_allclose(data.location(1).x, 250)  # first customer [x, y] location
    assert_allclose(data.location(1).y, 850)
    assert_allclose(data.location(1).delivery, 200)
    assert_allclose(data.location(1).tw_early, 3880)
    assert_allclose(data.location(1).tw_late, 9110)
    assert_allclose(data.location(1).service_duration, 100)
    assert_equal(vehicle_type.name, expected_name)

    # The data file specifies distances as 2D Euclidean. We take that and
    # should compute integer equivalents with up to one decimal precision.
    # For depot -> first customer:
    # For depot -> first customer:
    #      dX = 40 - 25 = 15
    #      dY = 50 - 85 = -35
    #      dist = sqrt(dX^2 + dY^2) = 38.07
    #      int(10 * dist) = 380
    assert_allclose(data.dist(0, 1), 380)
    assert_allclose(data.dist(1, 0), 380)

    for client in data.clients():
        assert_allclose(client.service_duration, 100)

        # This is a VRPTW instance, so all other fields should have their
        # default values.
        assert_allclose(client.release_time, 0)
        assert_allclose(client.prize, 0)
        assert_equal(client.required, True)


def test_warns_about_scaling_issues():
    """
    Tests that ``read()`` warns about scaling issues when a distance value is
    very large.
    """
    with assert_warns(ScalingWarning):
        # The arc from the depot to client 4 is really large (one billion), so
        # that should trigger a warning.
        read("data/ReallyLargeDistance.txt")


def test_round_func_trunc1_and_dimacs_are_same():
    """
    Tests that the DIMACS convention is equivalent to truncating to the first
    decimal.
    """
    trunc1 = read("data/RC208.txt", "solomon", "trunc1")
    dimacs = read("data/RC208.txt", "solomon", "dimacs")

    trunc1_dist = trunc1.distance_matrix()
    dimacs_dist = dimacs.distance_matrix()
    assert_allclose(trunc1_dist, dimacs_dist)

    trunc1_dur = trunc1.duration_matrix()
    dimacs_dur = trunc1.duration_matrix()
    assert_allclose(trunc1_dur, dimacs_dur)


def test_round_func_round_nearest():
    """
    Tests rounding to the nearest integer works well for the RC208 instance,
    which has Euclidean distances computed from integer coordinates. Since the
    instance is large, we'll test one particular distance.
    """
    data = read("data/RC208.txt", "solomon", "round")

    # We're going to test dist(0, 1) and dist(1, 0), which should be the same
    # since the distances are symmetric/Euclidean.
    assert_allclose(data.location(0).x, 40)
    assert_allclose(data.location(0).y, 50)

    assert_allclose(data.location(1).x, 25)
    assert_allclose(data.location(1).y, 85)

    # Compute the distance, and assert that it is indeed correctly rounded.
    dist = sqrt((40 - 25) ** 2 + (85 - 50) ** 2)
    assert_allclose(data.dist(0, 1), round(dist))
    assert_allclose(data.dist(1, 0), round(dist))


def test_service_time_specification():
    """
    Tests that specifying the service time as a specification (key-value pair)
    results in a uniform service time for all clients.
    """
    data = read("data/ServiceTimeSpecification.txt")

    # Clients should all have the same service time.
    services = [client.service_duration for client in data.clients()]
    assert_allclose(services, 360)


def test_multiple_depots():
    """
    Tests parsing a slightly modified version of the OkSmall instance, which
    now has two depots rather than one.
    """
    data = read("data/OkSmallMultipleDepots.txt")

    # Still five locations, but now with two depots and three clients.
    assert_equal(data.num_locations, 5)
    assert_equal(data.num_depots, 2)
    assert_equal(data.num_clients, 3)
    assert_equal(data.num_vehicle_types, 2)  # two, each at a different depot
    assert_equal(data.num_vehicles, 3)

    # First vehicle type should have two vehicles at the first depot.
    veh_type1 = data.vehicle_type(0)
    assert_equal(veh_type1.depot, 0)
    assert_equal(veh_type1.num_available, 2)

    # Second vehicle type should have one vehicle at the second depot.
    veh_type2 = data.vehicle_type(1)
    assert_equal(veh_type2.depot, 1)
    assert_equal(veh_type2.num_available, 1)

    depot1, depot2 = data.depots()

    # Test that the depot data has been parsed correctly. The first depot has
    # not changed.
    assert_allclose(depot1.x, 2_334)
    assert_allclose(depot1.y, 726)
    assert_allclose(depot1.tw_early, 0)
    assert_allclose(depot1.tw_late, 45_000)

    # But the second depot has the location data of what used to be the first
    # client, and a tighter time window than the other depot.
    assert_allclose(depot2.x, 226)
    assert_allclose(depot2.y, 1_297)
    assert_allclose(depot2.tw_early, 5_000)
    assert_allclose(depot2.tw_late, 20_000)


def test_mdvrptw_instance():
    """
    Tests that reading an MDVRPTW instance happens correctly, particularly the
    maximum route duration and multiple depot aspects.
    """
    data = read("data/PR11A.vrp", round_func="trunc")

    assert_equal(data.num_locations, 364)
    assert_equal(data.num_depots, 4)
    assert_equal(data.num_clients, 360)

    assert_equal(data.num_vehicles, 40)
    assert_equal(data.num_vehicle_types, 4)  # one vehicle type per depot

    for idx, vehicle_type in enumerate(data.vehicle_types()):
        # There should be ten vehicles for each depot, with the following
        # capacities and maximum route durations.
        assert_equal(vehicle_type.num_available, 10)
        assert_equal(vehicle_type.depot, idx)
        assert_allclose(vehicle_type.capacity, 200)
        assert_allclose(vehicle_type.max_duration, 450)

        # Essentially all vehicle indices for each depot, separated by a comma.
        # Each depot has ten vehicles, and they are nicely grouped (so the
        # first ten are assigned to the first depot, the second ten to the
        # second depot, etc.).
        expected_name = ",".join(str(10 * idx + veh + 1) for veh in range(10))
        assert_equal(vehicle_type.name, expected_name)

    # We haven't seen many instances with negative coordinates, but this
    # MDVRPTW instance has those. That should be allowed.
    assert_(any(depot.x < 0) for depot in data.depots())
    assert_(any(depot.y < 0) for depot in data.depots())
    assert_(any(client.x < 0) for client in data.clients())
    assert_(any(client.y < 0) for client in data.clients())


def test_vrpspd_instance():
    """
    Tests that reading an VRPSPD instance happens correctly, particularly the
    linehaul and backhaul data.
    """
    data = read("data/SmallVRPSPD.vrp", round_func="round")

    assert_equal(data.num_locations, 5)
    assert_equal(data.num_depots, 1)
    assert_equal(data.num_clients, 4)

    assert_equal(data.num_vehicles, 4)
    assert_equal(data.num_vehicle_types, 1)

    vehicle_type = data.vehicle_type(0)
    assert_equal(vehicle_type.num_available, 4)
    assert_allclose(vehicle_type.capacity, 200)

    # The first client is a linehaul client (only delivery, no pickup), and
    # the second client is a backhaul client (only pickup, no delivery). All
    # other clients have both delivery and pickup.
    deliveries = [1, 0, 16, 18]
    pickups = [0, 3, 10, 40]

    for idx, client in enumerate(data.clients()):
        assert_allclose(client.delivery, deliveries[idx])
        assert_allclose(client.pickup, pickups[idx])

    # Test that distance/duration are not set to a large value, as in VRPB.
    assert_allclose(np.max(data.distance_matrix()), 39)
    assert_allclose(np.max(data.duration_matrix()), 39)


def test_vrpb_instance():
    """
    Tests that reading an VRPB instance happens correctly, particularly the
    backhaul data and modified distances to ensure linehaul is served before
    backhaul.
    """
    data = read("data/X-n101-50-k13.vrp", round_func="round")

    assert_equal(data.num_locations, 101)
    assert_equal(data.num_depots, 1)
    assert_equal(data.num_clients, 100)

    assert_equal(data.num_vehicles, 100)
    assert_equal(data.num_vehicle_types, 1)

    vehicle_type = data.vehicle_type(0)
    assert_equal(vehicle_type.num_available, 100)
    assert_allclose(vehicle_type.capacity, 206)

    # The first 50 clients are linehaul, the rest are backhaul.
    clients = data.clients()

    for client in clients[:50]:
        assert_allclose(client.pickup, 0)
        assert_(client.delivery > 0)

    for client in clients[50:]:
        assert_(client.pickup > 0)
        assert_allclose(client.delivery, 0)

    # Tests that distance/duration from depot to backhaul clients is set to
    # ``MAX_VALUE``, as well as for backhaul to linehaul clients.
    linehauls = set(range(1, 51))
    backhauls = set(range(51, 101))

    for frm in range(data.num_locations):
        for to in range(data.num_locations):
            depot2back = frm == 0 and to in backhauls
            back2line = frm in backhauls and to in linehauls

            if depot2back or back2line:
                assert_allclose(data.dist(frm, to), MAX_VALUE)
                assert_allclose(data.duration(frm, to), MAX_VALUE)
            else:
                assert_(data.dist(frm, to) < MAX_VALUE)
                assert_(data.duration(frm, to) < MAX_VALUE)

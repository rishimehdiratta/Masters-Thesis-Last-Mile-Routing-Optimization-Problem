"""Capacited Vehicles Routing Problem (CVRP)."""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import haversine as hv
import pandas as pd

def distance_matrix(buyer_lat, buyer_long):
    return (hv.haversine(buyer_lat, buyer_long, unit=hv.Unit.METERS))


def create_data_model():
    """Stores the data for the problem."""
    data = {}
    # reading vehicle and customer data
    data_customer = pd.read_csv(
        r"C:\Users\Rishi Mehdiratta\Desktop\Data\Customer_Data.csv")
    data_vehicle = pd.read_csv(
        r"C:\Users\Rishi Mehdiratta\Desktop\Data\Vehicle_Data.csv")
    customers: str = data_customer.loc[0:249, "customer_id"]
    customers_set = list(customers)
    depot = 0
    nodes_set = [depot] + customers_set
    buyer_lat: float = data_customer.loc[0:249, "buyer_lat"]
    buyer_long: float = data_customer.loc[0:249, "buyer_long"]
    hub_lat: float = 28.65781432
    hub_long: float = 77.21996426
    nodes_coordinates = {}
    for i in range(len(customers_set)):
        nodes_coordinates.update({customers[i]: (buyer_lat[i], buyer_long[i])})
    nodes_coordinates[0] = (hub_lat, hub_long)
    distance_nodes = {}
    for n1 in nodes_set:
        for n2 in nodes_set:
            distance_nodes.update({(n1, n2): distance_matrix(nodes_coordinates[n1], nodes_coordinates[n2])})
    list_nodes = list(distance_nodes.values())
    dist_matx = [[list_nodes[n1] for n1 in range(len(nodes_set))] for n1 in range(len(nodes_set))]
    demands = [0] + list(data_customer.loc[0:249, "weight(Kg)"])
    veh_capacity = list(data_vehicle.loc[0:44, "Capacity(Kg)"])

    data['distance_matrix'] = dist_matx
    data['demands'] = demands
    data['vehicle_capacities'] = veh_capacity
    data['num_vehicles'] = 45
    data['depot'] = 0
    return data


def print_solution(data, manager, routing, solution):
    """Prints solution on console."""
    print(f'Objective: {solution.ObjectiveValue()}')
    total_distance = 0
    total_load = 0
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        route_distance = 0
        route_load = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_load += data['demands'][node_index]
            plan_output += ' {0} Load({1}) -> '.format(node_index, route_load)
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
        plan_output += ' {0} Load({1})\n'.format(manager.IndexToNode(index),
                                                 route_load)
        plan_output += 'Distance of the route: {}m\n'.format(route_distance)
        plan_output += 'Load of the route: {}\n'.format(route_load)
        print(plan_output)
        total_distance += route_distance
        total_load += route_load
    print('Total distance of all routes: {}m'.format(total_distance))
    print('Total load of all routes: {}'.format(total_load))


def main():
    """Solve the CVRP problem."""
    # Instantiate the data problem.
    data = create_data_model()

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(data['distance_matrix']),
                                           data['num_vehicles'], data['depot'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)


    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)


    # Add Capacity constraint.
    def demand_callback(from_index):
        """Returns the demand of the node."""
        # Convert from routing variable Index to demands NodeIndex.
        from_node = manager.IndexToNode(from_index)
        return data['demands'][from_node]

    demand_callback_index = routing.RegisterUnaryTransitCallback(
        demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        data['vehicle_capacities'],  # vehicle maximum capacities
        True,  # start cumul to zero
        'Capacity')

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.FromSeconds(1)

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if solution:
        print_solution(data, manager, routing, solution)


if __name__ == '__main__':
    main()
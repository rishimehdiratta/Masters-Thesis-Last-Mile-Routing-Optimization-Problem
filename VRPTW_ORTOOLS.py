"""Vehicles Routing Problem (VRP) with Time Windows."""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import haversine as hv
import pandas as pd

def distance_matrix(buyer_lat,buyer_long):
    return(hv.haversine(buyer_lat,buyer_long,unit = hv.Unit.METERS))

def create_data_model_1():
    """Stores the data for the problem."""

    # reading vehicle and customer data
    data_customer = pd.read_csv(
        r"C:\Users\Rishi Mehdiratta\Desktop\Customer Data (Updated).csv")
    data_vehicle = pd.read_csv(
        r"C:\Users\Rishi Mehdiratta\Desktop\Data\Vehicle_Data.csv")
    customers: str = data_customer.loc[:, "customer_id"]
    customers_set = list(customers)
    depot = 0
    nodes_set = [depot] + customers_set
    vehicle_data: str = data_vehicle.loc[0:17, "Vehicle Type"]
    vehicle_set = list(vehicle_data)

    buyer_lat: float = data_customer.loc[:, "buyer_lat"]
    buyer_long: float = data_customer.loc[:, "buyer_long"]
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
    #print(dist_matx)


    list_nodes = list(distance_nodes.values())
    #print(list_nodes)
    time_v = []
    for i in range(len(list_nodes)):
            time_v.append((list_nodes[i]/30))
    #print(time_v)
    time_nodes_list = [[int(time_v[n1]) for n1 in range(len(nodes_set))] for n1 in range(len(nodes_set))]
    #print(time_nodes_list)

    Earliest_time = {}
    E = data_customer.loc[:, "E"]
    for n in customers_set:
        Earliest_time.update({n: E[customers_set.index(n)]})
    #print(Earliest_time)

    Latest_time = {}
    L = data_customer.loc[:, "L"]
    for n in customers_set:
        Latest_time.update({n: L[customers_set.index(n)]})
    # print(Latest_time)
    time_gap = {}
    time_gap[0] = (0,720)

    for n in customers_set:
        time_gap.update({n: (Earliest_time[n], Latest_time[n])})

    #print(time_gap)
    time_windows = list(time_gap.values())
    #print(time_windows)

    #print(time_nodes_list)
    #print(time_windows)

    data = {}
    data['time_matrix'] = time_nodes_list
    data['time_windows'] = time_windows
    data['num_vehicles'] = len(vehicle_set)
    data['depot'] = 0
    return data


def print_solution(data, manager, routing, solution):
    """Prints solution on console."""
    print(f'Objective: {solution.ObjectiveValue()}')
    time_dimension = routing.GetDimensionOrDie('Time')
    total_time = 0
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        while not routing.IsEnd(index):
            time_var = time_dimension.CumulVar(index)
            plan_output += '{0} Time({1},{2}) -> '.format(
                manager.IndexToNode(index), solution.Min(time_var),
                solution.Max(time_var))
            index = solution.Value(routing.NextVar(index))
        time_var = time_dimension.CumulVar(index)
        plan_output += '{0} Time({1},{2})\n'.format(manager.IndexToNode(index),
                                                    solution.Min(time_var),
                                                    solution.Max(time_var))
        plan_output += 'Time of the route: {}min\n'.format(
            solution.Min(time_var))
        print(plan_output)
        total_time += solution.Min(time_var)
    print('Total time of all routes: {}min'.format(total_time))



"""Solve the VRP with time windows."""
# Instantiate the data problem.
data = create_data_model_1()

# Create the routing index manager.
manager = pywrapcp.RoutingIndexManager(len(data['time_matrix']),
                                        data['num_vehicles'], data['depot'])

# Create Routing Model.
routing = pywrapcp.RoutingModel(manager)


# Create and register a transit callback.
def time_callback(from_index, to_index):
    """Returns the travel time between the two nodes."""
    # Convert from routing variable Index to time matrix NodeIndex.
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)
    return data['time_matrix'][from_node][to_node]

transit_callback_index = routing.RegisterTransitCallback(time_callback)

# Define cost of each arc.
routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

# Add Time Windows constraint.
time = 'Time'
routing.AddDimension(
    transit_callback_index,
    10,  # allow waiting time
    720,  # maximum time per vehicle
    False,  # Don't force start cumul to zero.
    time)
time_dimension = routing.GetDimensionOrDie(time)


# Add time window constraints for each location except depot.
for location_idx, time_window in enumerate(data['time_windows']):
    if location_idx == data['depot']:
        continue
    index = manager.NodeToIndex(location_idx)
    time_dimension.CumulVar(index).SetRange(int(time_window[0]), int(time_window[1]))


# Add time window constraints for each vehicle start node.
depot_idx = data['depot']
for vehicle_id in range(data['num_vehicles']):
    index = routing.Start(vehicle_id)
    time_dimension.CumulVar(index).SetRange(
        data['time_windows'][depot_idx][0],
        data['time_windows'][depot_idx][1])

# Instantiate route start and end times to produce feasible times.
for i in range(data['num_vehicles']):
    routing.AddVariableMinimizedByFinalizer(
        time_dimension.CumulVar(routing.Start(i)))
    routing.AddVariableMinimizedByFinalizer(
        time_dimension.CumulVar(routing.End(i)))



# Setting first solution heuristic.
search_parameters = pywrapcp.DefaultRoutingSearchParameters()
search_parameters.first_solution_strategy = (
    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

# Solve the problem.
#routing.EnableOutput()
solution = routing.SolveWithParameters(search_parameters)

# Print solution on console.
if solution:
    print_solution(data, manager, routing, solution)


#if __name__ == '__main__':
#main()

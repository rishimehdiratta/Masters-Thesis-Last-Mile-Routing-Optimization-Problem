import haversine as hv
import pandas as pd
import pulp as pl
from pulp import GUROBI  # solver

def distance_matrix(buyer_lat, buyer_long):
    return (hv.haversine(buyer_lat, buyer_long,
                         unit=hv.Unit.KILOMETERS))  # distance function which returns distance between two points in KMs.


def main():
    m = 80    #number of nodes
    n = 5     #number of vehicles

    # reading customer data
    customer_data = pd.read_csv(r"C:\Users\Rishi Mehdiratta\Desktop\Data\Customer_Data.csv")

    # reading vehicle data
    vehicle_data = pd.read_csv(r"C:\Users\Rishi Mehdiratta\Desktop\Data\Vehicle_Data.csv")

    # SETS
    customers = list(customer_data.loc[0:m, "customer_no"])  # set of customers
    M = 20000

    vehicles = list(vehicle_data.loc[0:n, "Vehicle Type"])  # set of vehicles:

    depot = 0  # depot denoted as 0

    nodes = [depot] + customers  # set of nodes including depot

    ############################################################################################################################################

    # ---------------------PARAMETERS_START----------------------------#

    # values for calculating distance
    buyer_lat: float = customer_data.loc[0:m, "buyer_lat"]  # reading buyer lat
    buyer_long: float = customer_data.loc[0:m, "buyer_long"]  # reading buyer long

    hub_lat: float = 28.65781432  # reading hub lat
    hub_long: float = 77.21996426  # reading hub long

    # Parameter-1
    nodes_coordinates = {}  # dictionary which have customers as keys and a tuple containing there lat and long as values

    nodes_coordinates[0] = (hub_lat, hub_long)
    for i in customers:
        nodes_coordinates.update({i: (buyer_lat[customers.index(i)], buyer_long[customers.index(i)])})

    # Parameter - 2
    demand: float = customer_data.loc[0:m, "weight(Kg)"]  # reading demand of each customer

    demand_node = {}  # dictionary whose keys are customers and values as there respective demands
    for i in customers:
        demand_node.update({i: demand[customers.index(i)]})

    # Parameter - 3
    service_time: int = customer_data.loc[0:m, "transaction_time(mins)"]  # reading transaction time/service time of each node

    service_time_node = {}  # dictionary whose key values are customers and values as service times
    service_time_node[0] = 0  # S_0
    for i in customers:
        service_time_node.update({i: service_time[customers.index(i)]})

    # Parameter - 4
    free_km: int = vehicle_data.loc[0:n, "Free KMs"]  # set of freekms of vehicles:

    free_km_vehicle = {}  # dictionary whose key values are vehicles and values as freekms of vehicles
    for v in vehicles:
        free_km_vehicle.update({v: free_km[vehicles.index(v)]})

    # Parameter - 5
    maximum_capacity: int = vehicle_data.loc[0:n, "Capacity(Kg)"]

    maximum_capacity_vehicle = {}  # maximum capacity a vehicle can take in a trip
    for v in vehicles:
        maximum_capacity_vehicle.update({v: maximum_capacity[vehicles.index(v)]})

    # Parameter - 6
    fixed_cost: float = vehicle_data.loc[0:n, "Fixed Cost"]

    fixed_cost_vehicle = {}
    for v in vehicles:
        fixed_cost_vehicle.update({v: fixed_cost[vehicles.index(v)]})

    # Parameter - 7
    distance_nodes = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                distance_nodes.update({(i, j): float(distance_matrix(nodes_coordinates[i], nodes_coordinates[j]))})

    # Parameter - 8
    max_kms: int = vehicle_data.loc[0:n, "Max KMs (per day)"]

    max_kms_vehicle = {}  # maximum kms a vehicle can travel
    for v in vehicles:
        max_kms_vehicle.update({v: max_kms[vehicles.index(v)]})

    # Parameter - 9
    max_time: int = vehicle_data.loc[0:n, "Max Time(hrs)"]

    max_time_vehicle = {}  # maximum time a vehicle can take to deliver products
    for v in vehicles:
        max_time_vehicle.update({v: max_time[vehicles.index(v)]})

    # Parameter - 10
    speed: int = vehicle_data.loc[0:n, "uniform speed (km/min)"]

    speed_vehicle = {}  # speed per vehicle
    for v in vehicles:
        speed_vehicle.update({v: speed[vehicles.index(v)]})

    # Parameter - 11
    variable_cost: float = vehicle_data.loc[0:n, "Variable Cost"]

    variable_cost_vehicle = {}
    for v in vehicles:
        variable_cost_vehicle.update({v: variable_cost[vehicles.index(v)]})

    # Parameter - 12
    max_customer: int = vehicle_data.loc[0:n, "Max Buyers/Customers (in a trip)"]

    max_customer_vehicle = {}  # maximum number of customers a vehicle can serve with in a day
    for v in vehicles:
        max_customer_vehicle.update({v: max_customer[vehicles.index(v)]})

    # Parameter - 13
    max_demand: int = vehicle_data.loc[0:n, "Max Weight per Buyer/Customer"]

    max_demand_vehicle = {}  # maximum demand a vehicle can deliver for each buyer
    for v in vehicles:
        max_demand_vehicle.update({v: max_demand[vehicles.index(v)]})

    # Parameter - 14
    min_demand: int = vehicle_data.loc[0:n, "Min Weight per Buyer/Customer"]

    min_demand_vehicle = {}  # minimum demand a vehicle can deliver for each buyer
    for v in vehicles:
        min_demand_vehicle.update({v: min_demand[vehicles.index(v)]})

    time_nodes = {}  # time between two nodes
    for v in vehicles:
        for i in nodes:
            for j in nodes:
                if i != j:
                    time_nodes.update({(i, j, v): distance_nodes[i, j] / speed_vehicle[v]})

    earliest_time = customer_data.loc[0:m, "E"]       #converted the given time frames into integers (Earliest Time)
    latest_time = customer_data.loc[0:m, "L"]         #Latest Time
    earliest_time_dict = {}
    latest_time_dict = {}
    for i in customers:
        earliest_time_dict.update({i: earliest_time[customers.index(i)]})
    for i in customers:
        latest_time_dict.update({i: latest_time[customers.index(i)]})
    # ---------------------------PARAMETERS_END----------------------------#
    ##########################################################################################################

    # ----------------------DECISION_VARIABLES_START-----------------------#

    # dv-1
    vehicle_route = {}  # A decision variable that decides if vehicle v has taken route  i->j or not.

    for v in vehicles:
        for i in nodes:
            for j in nodes:
                if i != j:
                    vehicle_route.update({(i, j, v): pl.LpVariable(
                            "x" + "_" + str(i) + "_" + str(j) + "_" + str(v), cat="Binary")})

    # dv-2
    extra_kms = {}  # A decision variable that calculates extra km that vehicle v will travel in its route.

    for v in vehicles:
        extra_kms.update({v: pl.LpVariable("extra_kms" + "_" + str(v), cat="Continuous", lowBound=0)})

    # dv-3
    distance = {}  # total distance traveled by vehicle v in its journey
    for v in vehicles:
        aux_sum_1 = 0
        for i in nodes:
            for j in nodes:
                if i != j:
                    aux_sum_1 += distance_nodes[i, j] * vehicle_route[i, j, v]
        distance.update({v: aux_sum_1})

    # dv-4
    vehicle_use = {}  # A decision variable that indicates whether the vehicle v is used or not.

    for v in vehicles:
        vehicle_use.update({v: pl.LpVariable("u" + "_" + str(v), cat="Binary")})

    # dv-5
    vehicle_visit_node = {}  # A decision variable that indicates whether a vehicle v visited customer i or not.

    for v in vehicles:
        for i in nodes:
            vehicle_visit_node.update(
                    {(i, v): pl.LpVariable("y" + "_" + str(i) + "_" + str(v), cat="Binary")})

    # dv-6
    flow = {}  # A decision variable that indicates number of units of product in a vehicle v from node i to j
    for v in vehicles:
        for i in nodes:
            for j in nodes:
                if i != j:
                    flow.update({(i, j, v): pl.LpVariable(
                            "f" + "_" + str(i) + "_" + str(j) + "_" + str(v), cat="Continuous",
                            lowBound=0)})

    # dv-7
    start_time = {}  # A decision variable that indicates starting time of vehicle v visting node i

    for v in vehicles:
        for i in nodes:
            start_time.update({(i, v): pl.LpVariable("st" + "_" + str(i) + "_" + str(v),
                                                            cat="Continuous", lowBound=0)})

    # ----------------------DECISION_VARIABLES_END-----------------------#

    ############################################################################################################################################

    # problem definition
    prob = pl.LpProblem("Capacitated Vehicle Routing Problem with Time Windows", pl.LpMinimize)  # Minimization Problem

    ############################################################################################################################################

    # objective function

    aux_sum_2 = 0
    for v in vehicles:
        aux_sum_2 += ((variable_cost_vehicle[v] * extra_kms[v]) + (
                fixed_cost_vehicle[v] * vehicle_use[v]))  # To Minimize Cost

    prob += aux_sum_2

    #############################################################################################################################################

    # ----------------------CONSTRAINTS_START-----------------------#

    # constraint-1: this constraint finds the value of extra kms traveled,when extra_kms value is less than cumulative distance
    # traveled by vehicle then it becomes zero.

    for v in vehicles:
        prob += extra_kms[v] >= (distance[v] - free_km_vehicle[v])

    # ___________________________________________________________________________________________________________________________________________#

    # constraint-2: This constraint is a big M constraint which tells that if any vehicle v is in use then it has
    # atleast visited one node and if it is not in use, then the value of LHS becomes 0 because xijv is a binary
    # variable and has its lower bound zero.

    for v in vehicles:
        aux_sum_3 = 0
        for i in nodes:
            for j in nodes:
                if i != j:
                    aux_sum_3 += vehicle_route[i, j, v]
        prob += aux_sum_3 <= M * vehicle_use[v]

    # ___________________________________________________________________________________________________________________________________________#

    # constraint-3: This constraint says that each customer j in set C should be visited exactly once by any vehicle v.
    for j in customers:
        aux_sum_6 = 0
        for v in vehicles:
            aux_sum_6 += vehicle_visit_node[j, v]
        prob += aux_sum_6 == 1
    # ___________________________________________________________________________________________________________________________________________#

    # constraint-4: This constraint is a flow balancing constraint which tells that the number of vehicles coming in and out
    # of a customer’s location is same and it can only be by only one vehicle.

    for v in vehicles:
        for j in nodes:
            aux_sum_8 = 0
            aux_sum_9 = 0
            for i in nodes:
                if i != j:
                    aux_sum_8 += vehicle_route[i, j, v]
                    aux_sum_9 += vehicle_route[j, i, v]
            prob += aux_sum_8 == aux_sum_9
    # ___________________________________________________________________________________________________________________________________________#

    # constraint-5: This constraint is a flow balancing constraint which tells that the number of vehicles coming in and out
    # of a customer’s location is same and it can only be by only one vehicle.

    for v in vehicles:
        for i in nodes:
            aux_sum_10 = 0
            for j in nodes:
                if i != j:
                    aux_sum_10 += vehicle_route[i, j, v]
            prob += aux_sum_10 == vehicle_visit_node[i, v]
    # ___________________________________________________________________________________________________________________________________________#

    # constraint-6: This constraint tells that each customer should be visited only once that is entering node is just one.

    for v in vehicles:
        for i in nodes:
            aux_sum_21 = 0
            for j in nodes:
                if i != j:
                    aux_sum_21 += vehicle_route[j, i, v]
            prob += aux_sum_21 == vehicle_visit_node[i, v]
    # ___________________________________________________________________________________________________________________________________________#

    # constraint-7: This constraint says that every customer j demand must be bounded between the minimum and maximum demand,
    # any vehicle v can serve.

    for v in vehicles:
        for j in customers:
            prob += vehicle_visit_node[j, v] * min_demand_vehicle[v] <= demand_node[j] * vehicle_visit_node[
                    j, v] <= vehicle_visit_node[j, v] * max_demand_vehicle[v]
    # ___________________________________________________________________________________________________________________________________________#

    # constraint-8: This constraint says that the number of customers per vehicle v must be less than the maximum number of customers
    # it can serve.

    for v in vehicles:
        aux_sum_12 = 0
        for j in customers:
            aux_sum_12 += vehicle_visit_node[j, v]
        prob += aux_sum_12 <= max_customer_vehicle[v] + 1
    # ___________________________________________________________________________________________________________________________________________#

    # constraint-7: This constraint is demand satisfaction Constraint.

    for j in customers:
        aux_sum_13 = 0
        aux_sum_14 = 0
        for v in vehicles:
            for i in nodes:
                if i != j:
                    aux_sum_13 += flow[i, j, v]
                    aux_sum_14 += flow[j, i, v]
        aux_sum = aux_sum_13 - aux_sum_14
        prob += aux_sum == demand_node[j]

    # ___________________________________________________________________________________________________________________________________________#

    # constraint-8: This constraint tells that flow in an arc must be less than the maximum capacity of vehicle if that arc i->j is traversed.

    for v in vehicles:
        for i in nodes:
            for j in nodes:
                if i != j:
                    prob += flow[i, j, v] <= maximum_capacity_vehicle[v] * vehicle_route[i, j, v]
    # ___________________________________________________________________________________________________________________________________________#

    # constraint-9: Time Window Constraints.

    for v in vehicles:
        for i in nodes:
            for j in customers:
                if i != j:
                    prob += start_time[i, v] + service_time_node[i] + time_nodes[i, j, v] <= start_time[
                            j, v] + 720 * (1 - vehicle_route[i, j, v])

    # ___________________________________________________________________________________________________________________________________________#

    # Constraint-10: Vehicle must visit in time windows of customers.

    for v in vehicles:
        for i in customers:
            prob += earliest_time_dict[i] * vehicle_visit_node[i, v] <= start_time[i, v] <= latest_time_dict[
                    i] * vehicle_visit_node[i, v]

    # ___________________________________________________________________________________________________________________________________________#

    # Constraint-11: Bound on total time spent by vehicle in its route and total distnace travelled by vehicle.
    for v in vehicles:
        prob += distance[v] <= max_kms_vehicle[v]

    # ___________________________________________________________________________________________________________________________________________#

    ###########################################################################################################################################
    # solving the problem

    prob.writeLP("CVRPTW.lp")
    # print(prob)
    prob.solve(GUROBI(MIPFocus=1, Heuristics=0.5, MIPgap=0.2, Symmetry=2, timeLimit=1800, SolFiles='sol_', Method = -1))
    print(pl.LpStatus[prob.status])
    print(pl.value(prob.objective))

    # printing x_i_j_v
    for v in vehicles:
        for i in nodes:
            for j in nodes:
                if i != j:
                    if vehicle_route[i, j, v].value() > 0.0:
                        print(f" route {i} _ {j} _ {v} :{vehicle_route[i, j, v].value()}")
                        print(f" flow {i} _ {j} _ {v}  : {flow[i, j, v].value()}")
                        print("_________________________________________________________________")

main()
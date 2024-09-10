# Global sets
set FACILITIES; # set of facilities
set CUSTOMERS;  # set of customers
set SCENARIOS;  # set of scenarios

# Global parameters
param customer_demand{CUSTOMERS, SCENARIOS} >= 0;   # customer_demand of customer j in scenario s
param facility_capacity{FACILITIES} >= 0;           # facility_capacity of facility_open i


### SUBPROBLEM ###

# Subproblem parameters
param variable_cost{FACILITIES, CUSTOMERS} >= 0;    # variable cost of satisfying customer_demand of customer j from facility_open i

# Bender's parameters
param sub_facility_open{FACILITIES} binary default 0; # 1 if facility i is open, 0 otherwise
param sub_scenario symbolic in SCENARIOS;

# Subproblem variables
var production{FACILITIES, CUSTOMERS, s in SCENARIOS: s == sub_scenario} >= 0;  # production from facility i to satisfy customer demand j in scenario s

# Subproblem objective
minimize operating_cost: 
    sum{i in FACILITIES, j in CUSTOMERS} variable_cost[i,j]*production[i,j,sub_scenario]; 

# Subproblem constraints
s.t. satisfying_customer_demand{j in CUSTOMERS}:
    sum{i in FACILITIES} production[i,j,sub_scenario] >= customer_demand[j,sub_scenario];

s.t. facility_capacity_limits{i in FACILITIES}:
    sum{j in CUSTOMERS} production[i,j,sub_scenario] <= facility_capacity[i] * sub_facility_open[i];



### MASTER PROBLEM ### 

# Master parameters
param fixed_cost{FACILITIES} >= 0;               # fixed cost of opening facility_open i
param prob{SCENARIOS} default 1/card(SCENARIOS); # probability of scenario s

# Bender's parameters
param nITER >= 0 integer;
param cut_type {1..nITER, SCENARIOS} symbolic within {"opt", "feas", "none"};
param customer_price{CUSTOMERS, SCENARIOS, 1..nITER} >= 0;  # dual variable for the demand constraint
param facility_price{FACILITIES, SCENARIOS, 1..nITER} <= 0; # dual variable for the capacity constraint

# Master variables
var sub_variable_cost{SCENARIOS} >= 0; # subproblem objective bound
var facility_open{FACILITIES} binary;  # 1 if facility i is open, 0 otherwise

# Master objective
minimize total_cost: 
    sum{i in FACILITIES} fixed_cost[i]*facility_open[i] + sum{s in SCENARIOS} prob[s]*sub_variable_cost[s];

# Master constraints
s.t. sufficient_production_capacity:
    sum{i in FACILITIES} facility_capacity[i]*facility_open[i] >= max{s in SCENARIOS} sum{j in CUSTOMERS} customer_demand[j,s];

s.t. optimality_cut {k in 1..nITER, s in SCENARIOS: cut_type[k,s] == "opt"}:
        sum{j in CUSTOMERS} customer_price[j,s,k]*customer_demand[j,s] + 
        sum{i in FACILITIES} facility_price[i,s,k]*facility_capacity[i]*facility_open[i] <= sub_variable_cost[s]; 

s.t. feasibility_cut {k in 1..nITER, s in SCENARIOS: cut_type[k,s] == "feas"}: 
        sum{j in CUSTOMERS} customer_price[j,s,k]*customer_demand[j,s] + 
        sum{i in FACILITIES} facility_price[i,s,k]*facility_capacity[i]*facility_open[i] <= 0; 

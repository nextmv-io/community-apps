 set R; # Set of regions.

# Parameters
param cost_waste; # Cost per wasted product.
param cost_transport {R}; # Cost of transport to each region.
param price_min; # Minimum price for the product.
param price_max; # Maximum price for the product.
param quantity_min {R}; # Minimum quantity for each region.
param quantity_max {R}; # Maximum quantity for each region.
param total_amount_of_supply; # Total amount of supply.
param coefficients_intercept; # Intercept of the product demand model.
param coefficients_region {R}; # Region coefficients of the product demand model.
param coefficients_price; # Price coefficient of the product demand model.
param coefficients_year_index; # Year index coefficient of the product demand model.
param coefficients_peak; # Peak coefficient of the product demand model.
param data_year; # Year of the data.
param data_peak; # Peak of the data.

# Variables
var price {r in R} >= price_min, <= price_max;
var quantity {r in R} >= quantity_min[r], <= quantity_max[r];

# Define the demand function
var demand_expr {r in R} =
    coefficients_intercept +
    coefficients_region[r] +
    coefficients_price * price[r] +
    coefficients_year_index * (data_year - 2015) +
    coefficients_peak * data_peak;

var sales {r in R} = min(demand_expr[r],quantity[r]);
var revenue {r in R} = sales[r] * price[r];
var waste {r in R} = quantity[r] - demand_expr[r];
var costs {r in R} = cost_waste * waste[r] + cost_transport[r] * quantity[r];

# Objective
maximize obj: sum {r in R} (revenue[r] - costs[r]);

# Supply constraint checks that the sum of the quantities is equal to the total supply
subject to supply: sum {r in R} quantity[r] = total_amount_of_supply;  

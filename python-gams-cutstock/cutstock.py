"""
@file
This example implements a column generation approach to solve the
cutting stock problem. In this example, the column generation approach
has been entirely implemented in the program using GamsJob for the
master and GamsModelInstance for the pricing problem. GAMS is used to
build the master and pricing problems. The logic of the column
generation method is in the application program.
"""

import importlib.util
import os
from gams import GamsModifier, GamsWorkspace

GAMS_MASTER_MODEL = """
Set i 'widths';

Parameter
   w(i) 'width'
   d(i) 'demand';

Scalar
   r 'raw width';

$gdxIn csdata
$load i w d r
$gdxIn

$if not set pmax $set pmax 1000
Set
   p     'possible patterns' / 1*%pmax% /
   pp(p) 'dynamic subset of p';

Parameter
   aip(i,p) 'number of width i in pattern growing in p';

Variable
   xp(p) 'patterns used'
   z     'objective variable';

Integer Variable xp;
xp.up(p) = sum(i, d(i));

Equation
   numpat
   demand(i);

   numpat..    z =e= sum(pp, xp(pp));

   demand(i).. sum(pp, aip(i,pp)*xp(pp)) =g= d(i);

Model master / numpat, demand /;
"""

GAMS_SUB_MODEL = """
Set i 'widths';

Parameter w(i) 'width';
Scalar r 'raw width';

$gdxIn csdata
$load i w r
$gdxIn

Parameter
   demdual(i) 'duals of master demand constraint' / #i eps /;

Variable
   z
   y(i) 'new pattern';
Integer Variable y;
y.up(i) = ceil(r/w(i));

Equation
   defobj
   knapsack;

defobj..   z =e= 1 - sum(i, demdual(i)*y(i));

knapsack.. sum(i, w(i)*y(i)) =l= r;

Model pricing / defobj, knapsack /;
"""


def cutStockModel(
    d: dict,
    w: dict,
    r: int,
    max_pattern: int,
):
    """
    Args:
        d: demand
        w: width
        r: raw width
        max_pattern
    """
    spec = importlib.util.find_spec("gamspy_base")
    if spec and spec.origin:
        sys_dir = os.path.dirname(spec.origin)
    else:
        raise Exception(">gamspy_base< not found! Quiting.")

    ws = GamsWorkspace(system_directory=sys_dir)

    opt = ws.add_options()
    cutstock_data = ws.add_database("csdata")
    opt.all_model_types = "Cplex"
    opt.optcr = 0.0  # solve to optimality

    opt.defines["pmax"] = str(max_pattern)
    opt.defines["solveMasterAs"] = "RMIP"

    raw_width = cutstock_data.add_parameter("r", 0, "raw width")
    raw_width.add_record().value = int(r)

    demand = cutstock_data.add_parameter("d", 1, "demand")
    widths = cutstock_data.add_set("i", 1, "widths")
    for k, v in d.items():
        widths.add_record(k)
        demand.add_record(k).value = v

    width = cutstock_data.add_parameter("w", 1, "width")
    for k, v in w.items():
        width.add_record(k).value = v

    cp_master = ws.add_checkpoint()
    job_master_init = ws.add_job_from_string(GAMS_MASTER_MODEL)
    job_master_init.run(opt, cp_master, databases=cutstock_data)
    job_master = ws.add_job_from_string(
        "execute_load 'csdata', aip, pp; solve master min z using %solveMasterAs%;",
        cp_master,
    )

    pattern = cutstock_data.add_set("pp", 1, "pattern index")
    pattern_data = cutstock_data.add_parameter("aip", 2, "pattern data")

    if max_pattern < len(d):
        raise Exception(
            f"Maximum patterns ({max_pattern}) cannot be less than number of products ({len(d)})."
        )

    # initial pattern: pattern i hold width i
    pattern_count = 0
    for k, v in w.items():
        pattern_count += 1
        pattern_data.add_record(
            (k, pattern.add_record(str(pattern_count)).key(0))
        ).value = (int)(r / v)

    cp_sub = ws.add_checkpoint()
    job_sub = ws.add_job_from_string(GAMS_SUB_MODEL)
    job_sub.run(opt, cp_sub, databases=cutstock_data)
    mi_sub = cp_sub.add_modelinstance()

    # define modifier demdual
    demand_dual = mi_sub.sync_db.add_parameter(
        "demdual", 1, "dual of demand from master"
    )
    mi_sub.instantiate("pricing min z using mip", GamsModifier(demand_dual), opt)

    # find new pattern
    list_of_new_patterns = []
    patternFlag = False
    while True:
        job_master.run(opt, cp_master, databases=cutstock_data)
        # copy duals into mi_sub.sync_db DB
        demand_dual.clear()
        for dem in job_master.out_db["demand"]:
            demand_dual.add_record(dem.key(0)).value = dem.marginal
        mi_sub.solve()
        if mi_sub.sync_db["z"].first_record().level < -0.00001:
            if pattern_count == max_pattern:
                patternFlag = True
                print(
                    f"Out of pattern. Increase max_pattern (currently {max_pattern})."
                )
                break
            else:
                new_pattern = mi_sub.sync_db["z"].first_record().level
                list_of_new_patterns.append(new_pattern)
                print(f"New pattern! Value: {new_pattern}")
                pattern_count += 1
                s = pattern.add_record(str(pattern_count))
                for y in mi_sub.sync_db["y"]:
                    if y.level > 0.5:
                        pattern_data.add_record((y.key(0), s.key(0))).value = round(
                            y.level
                        )
        else:
            break

    # solve final MIP
    opt.defines["solveMasterAs"] = "MIP"
    job_master.run(opt, databases=cutstock_data)
    obj_val = job_master.out_db["z"].first_record().level
    print(f"Objective Value: {obj_val}")
    cuts = {}
    for xp in job_master.out_db["xp"]:
        if xp.level > 0.5:
            print(f"  pattern {xp.key(0)} {xp.level} times:")
            aip = job_master.out_db["aip"].first_record((" ", xp.key(0)))
            cuts[f"Pattern {xp.key(0)}"] = {"ncuts": xp.level, "itemCut": None}
            icut = {}
            while True:
                icut[aip.key(0)] = aip.value
                print(f"    {aip.key(0)}: {aip.value}")
                if not aip.move_next():
                    break
            cuts[f"Pattern {xp.key(0)}"]["itemCut"] = icut

    return ([patternFlag, list_of_new_patterns], int(obj_val), cuts)


if __name__ == "__main__":
    demand = {"Kraft": 97, "Newsprint": 610, "Coated": 395, "Lightweight": 211}
    width = {"Kraft": 47, "Newsprint": 36, "Coated": 31, "Lightweight": 14}
    raw_width = 100
    max_pattern = 35

    [_, list_of_new_patterns], obj_val, cut_info = cutStockModel(
        d=demand, w=width, r=raw_width, max_pattern=max_pattern
    )

    print(f"New patterns: {list_of_new_patterns}")
    print(f"Objective value: {obj_val}")
    print(f"Cut info: {cut_info}")

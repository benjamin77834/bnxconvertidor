# src/codegen/stepfunctions_codegen.py
"""
Generates AWS Step Functions workflow JSON from DAG.
Maps the execution order to a state machine with parallel branches.
"""
import json
from datetime import datetime


def generate_stepfunctions(dag, output_path, xfr_rules=None):
    xfr_rules = xfr_rules or {}
    states = {}
    order = [n.id for n in dag.execution_order]

    # Mega-DAG: group by graph boundary first, then by depth
    graph_boundaries = getattr(dag, 'graph_boundaries', {})

    # Group nodes by depth (parallel execution within same depth)
    depth_map = {}
    def get_depth(nid, visited=None):
        if visited is None: visited = set()
        if nid in visited: return 0
        visited.add(nid)
        node = dag.nodes.get(nid)
        if not node or not node.parents: return 0
        return 1 + max(get_depth(p, set(visited)) for p in node.parents if p in dag.nodes)

    for nid in order:
        d = get_depth(nid)
        if d not in depth_map: depth_map[d] = []
        depth_map[d].append(nid)

    # Build state machine
    sorted_depths = sorted(depth_map.keys())
    step_names = []

    for i, depth in enumerate(sorted_depths):
        nodes_at_depth = depth_map[depth]
        step_name = f"Phase_{depth}"
        step_names.append(step_name)

        if len(nodes_at_depth) == 1:
            nid = nodes_at_depth[0]
            node = dag.nodes[nid]
            ntype = node.type.upper()
            states[step_name] = {
                "Type": "Task",
                "Resource": f"arn:aws:states:::glue:startJobRun.sync",
                "Parameters": {
                    "JobName.$": f"$.jobs.{nid}",
                    "Arguments": {
                        "--node_id": nid,
                        "--node_type": ntype,
                    }
                },
                "ResultPath": f"$.results.{nid}",
            }
        else:
            # Parallel execution
            branches = []
            for nid in nodes_at_depth:
                node = dag.nodes[nid]
                ntype = node.type.upper()
                branches.append({
                    "StartAt": nid,
                    "States": {
                        nid: {
                            "Type": "Task",
                            "Resource": "arn:aws:states:::glue:startJobRun.sync",
                            "Parameters": {
                                "JobName.$": f"$.jobs.{nid}",
                                "Arguments": {
                                    "--node_id": nid,
                                    "--node_type": ntype,
                                }
                            },
                            "End": True,
                        }
                    }
                })
            states[step_name] = {
                "Type": "Parallel",
                "Branches": branches,
                "ResultPath": f"$.results.phase_{depth}",
            }

    # Chain phases
    for i, name in enumerate(step_names):
        if i < len(step_names) - 1:
            states[name]["Next"] = step_names[i + 1]
        else:
            states[name]["End"] = True

    workflow = {
        "Comment": f"BNX Generated Step Functions - {datetime.now().isoformat()}",
        "StartAt": step_names[0] if step_names else "End",
        "States": states,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(workflow, f, indent=2)

    return workflow

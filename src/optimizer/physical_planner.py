from src.physical.plan import PhysicalNode


class PhysicalPlanner:

    def plan(self, nodes):

        physical = []

        for n in nodes:

            t = n.type

            if t in ["INPUT"]:
                physical.append(PhysicalNode(
                    n.id, "scan", "parquet_scan", n.inputs, n.attrs
                ))

            elif t == "JOIN":

                # ? ENTERPRISE LOGIC (future cost model hook)
                strategy = "sort_merge_join"

                physical.append(PhysicalNode(
                    n.id, "join", strategy, n.inputs, n.attrs
                ))

            elif t in ["OUTPUT", "WRITE"]:
                physical.append(PhysicalNode(
                    n.id, "write", "parquet_write", n.inputs, n.attrs
                ))

            else:
                physical.append(PhysicalNode(
                    n.id, "generic", "passthrough", n.inputs, n.attrs
                ))

        return physical
from src.physical.plan import PhysicalNode


class CatalystOptimizer:

    def optimize(self, components):

        physical = []

        for c in components:

            t = c.type

            if t in ["INPUT", "SCAN"]:
                physical.append(
                    PhysicalNode(
                        id=c.id,
                        op_type="scan",
                        strategy="parquet_scan",
                        inputs=c.inputs,
                        attrs=c.attrs
                    )
                )

            elif t == "JOIN":
                physical.append(
                    PhysicalNode(
                        id=c.id,
                        op_type="join",
                        strategy="sort_merge_join",
                        inputs=c.inputs,
                        attrs=c.attrs
                    )
                )

            elif t in ["WRITE", "OUTPUT"]:
                physical.append(
                    PhysicalNode(
                        id=c.id,
                        op_type="write",
                        strategy="parquet_write",
                        inputs=c.inputs,
                        attrs=c.attrs
                    )
                )

            else:
                physical.append(
                    PhysicalNode(
                        id=c.id,
                        op_type="unsupported_" + t.lower(),
                        strategy="passthrough",
                        inputs=c.inputs,
                        attrs=c.attrs
                    )
                )

        return physical
def validate_dag(dag):

    errors = []

    all_nodes = set(dag.keys())

    for name, data in dag.items():

        for inp in data["inputs"]:

            if inp not in all_nodes:
                errors.append(f"❌ Missing dependency: {inp} -> {name}")

    # Detect orphan outputs
    for name, data in dag.items():
        if data["node"].type == "output" and not data["inputs"]:
            errors.append(f"❌ Output node {name} has no input")

    if errors:
        print("\n🚨 DAG VALIDATION FAILED")
        for e in errors:
            print(e)
        raise Exception("Invalid DAG")

    print("✔ DAG VALIDATION PASSED")
def parse_mp_file(path):

    dag = {}

    with open(path, "r", errors="replace") as f:
        for line in f:
            if "->" not in line:
                continue

            left, right = line.split("->")

            src = left.strip().replace(";", "")
            dst = right.strip().replace(";", "")

            dag.setdefault(dst, []).append(src)
            dag.setdefault(src, [])

    return dag
from collections import defaultdict

def build_upstream(edges):
    upstream = defaultdict(list)

    for s, d in edges:
        upstream[d].append(s)

    return upstream
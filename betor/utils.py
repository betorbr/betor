def jaccard_similarity(a: str, b: str) -> float:
    intersection_cardinality = len(set.intersection(*[set(a.lower()), set(b.lower())]))
    union_cardinality = len(set.union(*[set(a.lower()), set(b.lower())]))
    return intersection_cardinality / float(union_cardinality)

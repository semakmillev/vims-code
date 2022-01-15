def row_2_dict(rows, field='id'):
    return {r[field]: r for r in rows}


def group_by(rows, fields):
    res = {}


    for r in rows:
        key = (r[f] for f in fields) if isinstance(fields, list) else r[fields]
        try:
            res[key].append(r)
        except KeyError:
            res[key] = [r]
    return res

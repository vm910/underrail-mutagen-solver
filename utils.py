import multiprocessing as mp


def parallelize(func, args_list: list[tuple], num_workers: int = None) -> list:
    if num_workers is None:
        num_workers = min(4, mp.cpu_count() - 1)

    with mp.Pool(num_workers) as pool:
        results = pool.starmap(func, args_list)

    return results


def printd(d: dict) -> None:
    for key, value in d.items():
        print(key, *value, sep=" ")
    print("\n")


def flatten(l: list[list]) -> list:
    return [item for sublist in l for item in sublist]

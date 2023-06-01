from utils import *
import argparse
import logging
import colorlog
import concurrent.futures


EXITUS = []


def parse_reagents(path: str) -> dict:
    with open(path, "r") as f:
        reagents = f.readlines()
        reagents = [reagent.strip() for reagent in reagents]
        reagents = [reagent.split(" ") for reagent in reagents]
        mut_dict = dict(map(lambda reagents: (reagents[0], reagents[1:]), reagents))

        global EXITUS
        EXITUS = mut_dict.pop("Exitus-1")
        return mut_dict


def filter_useless_reagents(reagents: dict) -> dict:
    while True:
        reagents_c = reagents.copy()
        for key, reagent in reagents_c.items():
            for atom in reagent:
                if (
                    atom[0] != "-"
                    and atom not in EXITUS
                    and "-" + atom not in flatten(list(reagents_c.values()))
                    and key in reagents
                ):
                    reagents.pop(key)
                    break
        if reagents == reagents_c:
            break

    return reagents


def combine_reagents(reagent1: list[str], reagent2: list[str]) -> list[str]:
    r1 = reagent1.copy()
    r2 = reagent2.copy()

    r1 = [atom for atom in r1 if atom[0] != "-"]

    for atom in reagent1:
        if atom in reagent2:
            r2.remove(atom)

    for atom in reagent2:
        if atom[1:] in reagent1:
            r1.remove(atom[1:])
            r2.remove(atom)

    r2 = [atom for atom in r2 if atom[0] != "-"]

    return r1 + r2


def bfs(
    start_sequence: dict, reagents: dict, exitus: list[str], depth_limit=6
) -> list[str]:
    queue = [
        (start_sequence["name"], start_sequence["sequence"], [start_sequence["name"]])
    ]

    while queue:
        previous_name, current_sequence, path = queue.pop(0)

        if len(path) > depth_limit:
            break

        if current_sequence == exitus:
            return path

        for reagent_name, reagent_sequence in reagents.items():
            if reagent_name != previous_name:
                new_sequence = combine_reagents(current_sequence, reagent_sequence)
                queue.append((reagent_name, new_sequence, path + [reagent_name]))

    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Looks for a solution to the mutagen problem, using BFS."
    )

    handler = logging.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s - %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
            reset=True,
            style="%",
        )
    )
    logging.basicConfig(level=logging.INFO, handlers=[handler])

    parser.add_argument(
        "--reagents",
        type=str,
        dest="reagents",
        help="Path to the reagents file.",
        default="reagents.txt",
        required=True,
    )

    parser.add_argument(
        "--depth",
        type=int,
        dest="depth",
        help="Depth limit for the BFS.",
        default=6,
        required=False,
    )

    parser.add_argument(
        "--first",
        action="store_true",
        default=False,
        help="If set, only the first solution will be printed.",
    )

    args = parser.parse_args()

    logger = colorlog.getLogger()
    logger.info("Parsing reagents...")
    reagents = parse_reagents(args.reagents)
    logger.info("Filtering useless reagents...")
    filtered_reagents = filter_useless_reagents(reagents)

    logger.info("Searching...")
    with concurrent.futures.ProcessPoolExecutor() as executor:
        future_to_sequence = {
            executor.submit(
                bfs,
                {"name": key, "sequence": value},
                filtered_reagents,
                EXITUS,
                args.depth,
            ): key
            for key, value in filtered_reagents.items()
        }

        if args.first:
            done, not_done = concurrent.futures.wait(
                future_to_sequence, return_when=concurrent.futures.FIRST_COMPLETED
            )

            for future in done:
                key = future_to_sequence[future]
                try:
                    path = future.result()
                except Exception as exc:
                    logger.error(f"{key} generated an exception: {exc}")
                else:
                    if path is not None:
                        logger.info(f"Solution found for starter node {key}: {path}")
                        logger.info("Exiting...")
                        for future in not_done:
                            logger.info(f"Cancelling {future_to_sequence[future]}")
                            future.cancel()
                        break
        else:
            for future in concurrent.futures.as_completed(future_to_sequence):
                key = future_to_sequence[future]
                try:
                    path = future.result()
                except Exception as exc:
                    logger.error(f"{key} generated an exception: {exc}")
                else:
                    if path is None:
                        logger.warning(f"No solution found for starter node {key}")
                    else:
                        logger.info(f"Solution found for starter node {key}: {path}")

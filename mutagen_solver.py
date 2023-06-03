from utils import *
import argparse
import logging
import colorlog
import concurrent.futures


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Looks for a solution to the mutagen problem, using BFS."
    )

    handler = logging.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s %(asctime)s - %(message)s",
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

    parser.add_argument(
        "--debug",
        action="store_true",
        default=False,
        help="If set, the debug messages will be printed.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="If set, a step by step of the combinations will be printed out.",
    )

    parser.add_argument(
        "--start", type=str, help="The starting node for the BFS.", required=False
    )

    args = parser.parse_args()

    logging_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=logging_level, handlers=[handler])

    logger = colorlog.getLogger()

    logger.info("Parsing reagents...")
    reagents, EXITUS = parse_reagents(args.reagents)

    try:
        validate_reagents(reagents, EXITUS)
    except ValueError as e:
        logger.error(e)
        exit(1)

    if args.debug:
        logger.debug("Exitus:")
        print(f'\t{" ".join(map(str, EXITUS))}')
        logger.debug("Reagents:")
        printd(reagents)

    logger.info("Filtering useless reagents...")
    filtered_reagents = filter_useless_reagents(reagents, EXITUS)
    if args.debug:
        logger.debug("Useful reagents:")
        printd(filtered_reagents)

    logger.info("Searching...")
    if args.start:
        if args.start not in filtered_reagents:
            logger.error(f"Starter node {args.start} not found in reagents")
            exit(1)
        else:
            start = {"name": args.start, "sequence": filtered_reagents[args.start]}
            logger.info(f"Starting from {args.start}")
            path = bfs(start, filtered_reagents, EXITUS, args.depth, True)
            if path is None:
                logger.warning(f"No solution found for starter node {args.start}")
            else:
                logger.info(
                    f"Solution found for starter node {args.start}: [{' '.join(map(str, path))}]"
                )
                if args.verbose:
                    logger.info("Step by step:")
                    print_verbose_solution(reagents, path, EXITUS)
    else:
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
                            logger.info(
                                f"Solution found for starter node {key}: [{' '.join(map(str, path))}]"
                            )
                            if args.verbose:
                                logger.info("Step by step:")
                                print_verbose_solution(reagents, path, EXITUS)
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
                            logger.info(
                                f"Solution found for starter node {key}: [{', '.join(map(str, path))}]"
                            )
                            if args.verbose:
                                logger.info("Step by step:")
                                print_verbose_solution(reagents, path, EXITUS)

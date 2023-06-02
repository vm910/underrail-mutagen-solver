from colorama import Fore, Style


def printd(d: dict) -> None:
    for key, value in d.items():
        colored_values = [
            f"{Fore.RED}{atom}{Style.RESET_ALL}"
            if atom.startswith("-")
            else f"{Fore.GREEN}{atom}{Style.RESET_ALL}"
            for atom in value
        ]
        print(f"\t{key}: {' '.join(map(str, colored_values))}")
    print("\n")


def flatten(l: list[list]) -> list:
    return [item for sublist in l for item in sublist]


def parse_reagents(path: str) -> dict:
    with open(path, "r") as f:
        reagents = f.readlines()
        reagents = [reagent.strip() for reagent in reagents]
        reagents = [reagent.split(" ") for reagent in reagents]
        mut_dict = dict(map(lambda reagents: (reagents[0], reagents[1:]), reagents))

        EXITUS = mut_dict.pop("Exitus-1")
        return mut_dict, EXITUS


def filter_useless_reagents(reagents: dict, EXITUS: list[str]) -> dict:
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


def color_eliminated_atoms(reagent1: list[str], reagent2: list[str]):
    color_values1 = []
    color_values2 = []

    for atom in reagent1:
        if "-" + atom in reagent2:
            color_values1.append(f"{Fore.RED}{atom}{Style.RESET_ALL}")
        else:
            color_values1.append(atom)

    for atom in reagent2:
        if atom[1:] in reagent1:
            color_values2.append(f"{Fore.RED}{atom}{Style.RESET_ALL}")
        elif atom in reagent1:
            color_values2.append(atom)
        elif atom[0] != "-":
            color_values2.append(f"{Fore.CYAN}{atom}{Style.RESET_ALL}")
        else:
            color_values2.append(atom)

    return color_values1, color_values2


def exitus_difference(compound: list[str], exitus: list[str]) -> int:
    color_values = []

    for i, atom in enumerate(compound):
        if atom not in exitus:
            color_values.append(f"{Fore.RED}{atom}{Style.RESET_ALL}")
        elif atom in exitus and i != exitus.index(atom):
            color_values.append(f"{Fore.YELLOW}{atom}{Style.RESET_ALL}")
        else:
            color_values.append(f"{Fore.GREEN}{atom}{Style.RESET_ALL}")

    return color_values


def print_verbose_solution(
    reagents: dict, solution: list[str], exitus: list[str]
) -> None:
    compound = [atom for atom in reagents[solution[0]] if atom[0] != "-"]

    for i in range(1, len(solution)):
        colored_reagent1, colored_reagent2 = color_eliminated_atoms(
            compound, reagents[solution[i]]
        )
        print(f" {i}.\t  {' '.join(map(str, colored_reagent1))}")
        print(f"\t+ {' '.join(map(str, colored_reagent2))}")

        compound = combine_reagents(compound, reagents[solution[i]])

        print(f"\t= {' '.join(map(str, exitus_difference(compound, exitus)))}")
        print(f"\t  {' '.join(map(str, exitus))}")
        print("\n")


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

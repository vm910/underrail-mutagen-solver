from colorama import Fore, Style
import heapq


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
    removed_reagents = []

    while True:
        reagents_c = reagents.copy()
        atom_pool = set(flatten(list(reagents_c.values())))

        for key, reagent in reagents_c.items():
            for atom in reagent:
                if (
                    atom[0] != "-"
                    and atom not in EXITUS
                    and "-" + atom not in atom_pool
                    and key in reagents
                ):
                    reagents.pop(key)
                    removed_reagents.append(key)
                    break
        if reagents == reagents_c:
            break

    return reagents, removed_reagents


def combine_reagents(reagent1: list[str], reagent2: list[str]) -> list[str]:
    reagent1_set = set(reagent1)
    reagent2_set = set(reagent2)

    r1 = [
        atom for atom in reagent1 if atom[0] != "-" and "-" + atom not in reagent2_set
    ]
    r2 = [atom for atom in reagent2 if atom[0] != "-" and atom not in reagent1_set]

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
        elif atom[0] != "-" and atom not in reagent1:
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

    for i in range(0, len(solution)):
        if i == 0:
            print(f" {i}.\t  {' '.join(map(str, exitus_difference(compound, exitus)))}")
            print(f"\t  {' '.join(map(str, exitus))}")
            print()
        else:
            colored_reagent1, colored_reagent2 = color_eliminated_atoms(
                compound, reagents[solution[i]]
            )
            print(f" {i}.\t  {' '.join(map(str, colored_reagent1))}")
            print(f"\t+ {' '.join(map(str, colored_reagent2))}")

            compound = combine_reagents(compound, reagents[solution[i]])

            print(f"\t= {' '.join(map(str, exitus_difference(compound, exitus)))}")
            print(f"\t  {' '.join(map(str, exitus))}")
            print()


def validate_reagents(reagents: dict, exitus: list[str]) -> None:
    atom_pool = set(flatten(list(reagents.values())))

    for atom in exitus:
        if atom not in atom_pool:
            raise ValueError(f"Exitus atom {atom} not found in reagents")

def heuristic(current_sequence: list[str], target_sequence: list[str], depth: int) -> float:
    score = 0.0
    index_c = 0

    for i, atom in enumerate(current_sequence):
        target_index = i - index_c
        if len(target_sequence) >= i and atom == target_sequence[target_index]:
            score += 3 / depth
        else:
            score -= 1 * depth
            index_c += 1

    return score

def priority_search(
    start_sequence: dict, reagents: dict, exitus: list[str], depth_limit: int = 15
) -> list[str]:
    p_queue = []

    I = 0

    heapq.heappush(
        p_queue,
        (
            -heuristic(start_sequence["sequence"], exitus, 1),
            start_sequence["name"], 
            start_sequence["sequence"],
            [],
            [start_sequence["name"]]
        )
    )

    while p_queue:
        priority, previous_name, current_sequence, previous_sequence, path = heapq.heappop(p_queue)

        if len(path) >= depth_limit or I >= 2500:
            break
        
        for reagent_name, reagent_sequence in reagents.items():
            if reagent_name == previous_name:
                continue

            new_sequence = combine_reagents(current_sequence, reagent_sequence)
     
            if new_sequence == exitus:
                return path + [reagent_name]
            else:
                new_priority = heuristic(new_sequence, exitus, len(path + [reagent_name]))
                heapq.heappush(p_queue, (-new_priority, reagent_name, new_sequence, current_sequence, path + [reagent_name]))
        
        I += 1

    return None  

def contains_ordered_slice(sequence: list[str], target_slice: list[str]) -> bool:
    slice_length = len(target_slice)
    
    for i in range(len(sequence) - slice_length + 1):
        if sequence[i:i + slice_length] == target_slice:
            return True
    return False

def get_viable_start_reagents(reagents: dict, exitus: list[str]) -> dict:
    viable_starts = []

    for reagent_name, reagent_sequence in reagents.items():
        score = 0
        i = 1

        while contains_ordered_slice(reagent_sequence, exitus[:i]):
            score = i
            i += 1

        if score > 0:
            viable_starts.append((score, reagent_name, reagent_sequence))

        viable_starts.sort(reverse=True, key=lambda x: x[0])

    return viable_starts

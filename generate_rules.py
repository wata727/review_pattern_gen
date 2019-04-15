from json import dump, load
from configparser import ConfigParser
from difflib import ndiff
from prefixspan import PrefixSpan_frequent, PrefixSpan
import np
import pdb

config = ConfigParser()
config.read('config')
owner = config["Target"]["owner"]
repo = config["Target"]["repo"]
lang = config["Target"]["lang"]

INPUT_JSON_NAME = "data/changes/" + owner + "_" + repo + "_" + lang + ".json"
OUTPUT_JSON_NAME = "data/rules/" + owner + "_" + repo + "_" + lang + ".json"

def remove_redundant_symbols(code):
    tokens = []
    symbol = ""
    for token in code:
        start = token[0]
        if start == symbol:
            tokens[-1] = tokens[-1] + " " + token[2:]
        else:
            symbol = start
            tokens.append(token)

    return tokens

def remove_dup_changes(changes_sets):
    new_changes = []
    current_pull = 0
    for changes_set in changes_sets:
        if current_pull == changes_set["number"] and\
                changes_set["changes_set"] in list(map(lambda x: x["changes_set"], new_changes)):
            continue
        current_pull = changes_set["number"]
        new_changes.append(changes_set)
    return new_changes


def generate_rules(changes_sets, threshold):
    ps = PrefixSpan(changes_sets)
    print("Start rule generation")
    # freq_seqs = ps.frequent(minsup=int(len(new_changes) * 0.1), closed=True)
    freq_seqs = ps.frequent(minsup=threshold, closed=True)

    # freq_seqs = PrefixSpan_frequent(
    #     ps, minsup=int(len(new_changes) * 0.1), closed=True)
    freq_seqs = [x for x in freq_seqs
                 if any([y.startswith("+") for y in x[1]]) and
                 any([y.startswith("-") for y in x[1]])
                 ]

    freq_seqs = sorted(freq_seqs, reverse=True)
    return freq_seqs

def is_code_in_changes_set(changes_set, code):
    for i, _ in enumerate(changes_set):
        if changes_set[i:len(code) + i] == code:
            return True
    return False

with open(INPUT_JSON_NAME, mode='r', encoding='utf-8') as f:
    changes_sets = load(f)

changes_sets = remove_dup_changes(changes_sets)

# new_changes = []
# for tokens in changes:
#     new_tokens = [x for x in tokens
#                   if not x.endswith("\n") and not x.endswith(" ")]
#     if new_tokens != []:
#         new_changes.append(new_tokens)

changes = []
for changes_set in changes_sets:
    tokens = [x for x in changes_set["changes_set"] if not x.endswith("\n") and not x.endswith(" ")]
    changes_set["changes_set"] = tokens
    changes.append(changes_set)

freq_seqs = generate_rules(list(map(lambda x: x["changes_set"], changes)), 1)

new_rules = []

for i, rule in enumerate(freq_seqs):
    count = rule[0]
    code = rule[1]
    matches = [change for change in changes if is_code_in_changes_set(change['changes_set'], code)]
    trigger_tokens = list(np.hstack([x[2:].split(" ") if " " in x[2:] else [x[2:]] for x in code if not x.startswith("+")]))
    code = remove_redundant_symbols(code)
    new_rules.append({"count": count, "code": code, "trigger": trigger_tokens, "sources": list(map(lambda x: x['1-n_url'], matches))})

with open(OUTPUT_JSON_NAME, mode='w', encoding='utf-8') as f:
    dump(new_rules, f, indent=1)

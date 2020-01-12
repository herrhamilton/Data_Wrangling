import itertools
import collections
import re, csv

data_file ="restaurants.tsv"
gold_file = "restaurants_DPL.tsv"

def clean_address(entry):
    street_synonyms = {
        "north": "n",
        "south": "s",
        "east": "e",
        "west" : "w",
        "street": "st",
        "square": "sq",
        "plaza": "pl",
        "parkway": "pkwy",
        "highway": "hwy",
        "blv": "blvd",
        "streets": "sts",
        "avenues": "aves",
        "first": "1st",
        "second": "2nd",
        "third": "3rd",
        "fourth": "4th",
        "fifth": "5th",
        "sixth": "6th",
        "seventh": "7th",
        "eighth": "8th",
        "ninth": "9th",
        "tenth": "10th",
    }
    cleaned = entry
    clean_addr = []
    for x in entry["address"].split():
        clean_addr.append(street_synonyms[x] if x in street_synonyms else x)
    cleaned["address"] = " ".join(clean_addr)
    return cleaned

def split_in_phone_areas(data):
    areas = collections.defaultdict(list)
    for row in data:
        area_code = row["phone"][:3]
        areas[area_code].append(row)
    return [areas[x] for x in areas]

def find_duplicates(restaurants):
    dup_name = []
    dup_addr = []
    dup_phone = []

    buckets = split_in_phone_areas(restaurants)
    pp = 0
    for b in buckets:
        pairs = list(itertools.combinations(b, 2))
        pp += len(pairs)
        for p in pairs:
            id1 = p[0]["id"]
            id2 = p[1]["id"]
            if is_similar(p[0]["name"],p[1]["name"]):
                dup_name.append([id1, id2])
            if is_similar(p[0]["address"], p[1]["address"]):
                dup_addr.append([id1, id2])
            if p[0]["phone"] == p[1]["phone"]:
                dup_phone.append([id1, id2])
    return [pair for pair in dup_name if pair in (dup_addr+dup_phone)]

def is_similar(a, b):
    if a in b or b in a:
        return True
    words_a = set(a.split())
    words_b = set(b.split())
    if words_a.issubset(words_b) or words_b.issubset(words_a):
        return True
    return False

def compare_to_gold(duplicates, all_entries):
    gold_data = csv_parse(gold_file, "\t")
    positives = [[x["id1"], x["id2"]] for x in gold_data]

    missing = [x for x in positives if x not in duplicates]
    false = [x for x in duplicates if x not in positives]

    tpr = (len(positives)-len(missing)) / len(positives)
    tnr = ((all_entries-len(positives))-len(false)) / (all_entries-len(positives))
    balanced_accuracy = (tpr+tnr)/2

    print(("MISSING: {} / {}\n" + str(missing)).format(len(missing), len(positives)))
    print(("FALSE: {}\n" + str(false)).format(len(false)))
    print("BALANCED ACCURACY: {}".format(balanced_accuracy))

def csv_parse(file_in, delimiter):
    with open(file_in, mode='r', newline = '') as csv_file:
        csv_reader = csv.DictReader(csv_file, delimiter= delimiter)
        content = list()
        [content.append(x) for x in csv_reader]
        return content

def write_csv(file_out, delimiter, data):
    with open(file_out, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=delimiter,
                            quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(data[0].keys())
        [writer.writerow(list(x.values())) for x in data]

restaurants = csv_parse(data_file, "\t")
clean_restaurants = [clean_address(x) for x in restaurants]
duplicates = find_duplicates(clean_restaurants)
delete_ids = [x[1] for x in duplicates]
no_duplicates = [x for x in clean_restaurants if x["id"] not in delete_ids]
compare_to_gold(duplicates, len(clean_restaurants))
write_csv("clean_" + data_file, "\t", no_duplicates)
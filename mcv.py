# Maricom Variables Implementation

# MCV is a simple data file format. It's even simpler than INI. A valid key cannot start with # as this denotes a comment, but is allowed elsewhere in the key. A valid key cannot contain an = anywhere, but values can contain it. MCV Has no escape character parsing. While a MCV parser should reject any invalid file inputs, the reference parser has a lenient mode.

def save(data: dict, comment: str = None):
    text = []
    if comment:
        text.append(f"#{comment}")
    for key in data:
        if key.startswith("#"):
            raise ValueError("A valid key cannot start with # as this denotes a comment")
        if "=" in key:
            raise ValueError("A valid key cannot contain an = as this denotes the value pairing")
        text.append(f"{key}={data[key]}")
    out = "\n".join(text)
    return out

def load(mcv: str, strict_parsing: bool = False):
    splitfile = mcv.splitlines()
    dictionary = {}
    for pair in splitfile:
        splittup = pair.split("=", 1)
        if not pair or pair[0] == "#":
            continue
        elif not len(splittup) == 2:
            if strict_parsing:
                raise ValueError("Valueless key in MCV")
            else:
                print("Warning: Valueless key found, ignoring")
        else:
            if splittup[0] in dictionary:
                if strict_parsing:
                    raise ValueError("Duplicate key in MCV")
                else:
                    print("Warning: Duplicate key found, ignoring")
            else:
                dictionary[splittup[0]] = splittup[1]
    return dictionary
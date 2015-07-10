import re

class _Sketchy(object):
    def __getitem__(self, key):
        return key

MAGIC_selector_generator = _Sketchy()

def ser_str(sel):
    temp = str(sel)
    return temp[1:len(temp) - 1]

def syn_err(s, i):
    raise SyntaxError("deserialization of selector string failed -> bad syntax; s:{s}, i:{i}, s[i]:{s_i}".format(s=s, i=i, s_i=("\"%s\"" % s[i] if i < len(s) else "[out of bounds]")))

# get the digits from a tuple. starts after the first '('
def from_tuple(s, i, handle_none = False):
    numbers = []
    j = 0

    # accum digits from tuple
    while True:
        print("numbers:{numbers}".format(numbers=numbers))
        if s[i].isdigit() or (s[i] == "-" and len(numbers[j]) == 0):
            if len(numbers) <= j:
                numbers.append(s[i])
            else:
                numbers[j] += s[i]
            i += 1
            continue

        elif handle_none and len(s)>=i+4 and s[i:i+4] == "None":
            j += 1
            numbers.append(None)

        elif s[i] == ",":
            i += 1
            j += 1
            continue

        elif s[i] == ")":
            i += 1
            break

        else:
            syn_err(s, i)

    i += 1
    numbers = [(int(number) if not number is None else None) for number in numbers]
    return {"index": i, "numbers": numbers}


def deser_str(s):
    # recursive descent parser for numpy-esque array selector passed as a string
    selector = []
    s = re.sub("\s", "", s) # strip whitespace

    # strip useless parens
    while True:
        res = re.sub(r"\(([0-9]+(?::[0-9]+)*)\)", r"\1", s)
        if res != s:
            s = res
        else:
            break

    i = 0
    while i < len(s):
        # parse slice
        if s[i:i+6] == "slice(":
            i += 6

            res = from_tuple(s, i, handle_none=True)
            i = res["index"]
            numbers = res["numbers"]

            if len(numbers) < 1:
                syn_err(s, i)

            # we're either done or moving to another selector member

            if i <= len(s) and s[i] != ",":
                syn_err(s, i)

            if len(numbers) > 3:
                syn_err(s, i)

            selector.append(slice(*numbers))
            continue

        # parse tuple
        elif s[i] == "(":
            i += 1
            res = from_tuple(s, i)
            i = res["index"]
            numbers = res["numbers"]
            if len(numbers) < 1:
                syn_err(s, i)

            selector.append(numbers)
            continue

        elif s[i].isdigit():
            number = s[i]
            i += 1

            while i < len(s):
                if s[i].isdigit() or (s[i] == "-" and len(number) == 0):
                    number += s[i]
                    i += 1
                    continue

                elif s[i] == ",":
                    i += 1
                    break

                else:
                    syn_err(s, i)

            selector.append(int(number))
        else:
            syn_err(s, i)

    return selector


if __name__ == "__main__":
    print("base case")
    serd = ser_str((123, 123, slice(12, 120)))
    print(serd)
    print(deser_str(serd))

    print("base case 2")
    serd = ser_str((123, 123, slice(12, 120, 10)))
    print(serd)
    print(deser_str(serd))

    print("negative number")
    serd = ser_str((123, -123, slice(12, 120)))
    print(serd)
    print(deser_str(serd))

    print("negative step")
    serd = ser_str((123, 123, slice(12, 120, -1)))
    print(serd)
    print(deser_str(serd))
import re

class _Sketchy(object):
    def __getitem__(self, key):
        return key

MAGIC_selector_generator = _Sketchy()

def ser_str(sel):
    return str(sel)

# get the digits from a tuple. starts after the first '('
def from_tuple(s, i):
    numbers = []
    j = 0

    # accum digits from tuple
    while True:
        if s[i].isdigit():
            if len(numbers) < j:
                numbers.push(s[i])
            else:
                numbers[j] += s[i]
            i+=1
            continue

        if s[i] == ",":
            i+=1
            j+=1
            continue

        if s[i] == ")":
            i+=1
            break

        else:
            raise SyntaxError("deserialization of selector string failed -> bad syntax")

    i += 1
    numbers = [int(number) for number in numbers]
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

            res = from_tuple(s, i)
            i = res["index"]
            numbers = res["numbers"]
            if len(numbers) < 1:
                raise SyntaxError("deserialization of selector string failed -> bad syntax")

            # we're either done or moving to another selector member
            if not i < len(s) or s[i] != ",":
                raise SyntaxError("deserialization of selector string failed -> bad syntax")

            if len(numbers) > 3:
                raise SyntaxError("deserialization of selector string failed -> bad syntax")

            selector.push(slice(*numbers))
            continue

        # parse tuple
        elif s[i] == "(":
            res = from_tuple(s, i)
            i = res["index"]
            numbers = res["numbers"]
            if len(numbers) < 1:
                raise SyntaxError("deserialization of selector string failed -> bad syntax")

            selector.append(numbers)
            continue

        elif s[i].isdigit():
            number = s[i]
            i += 1

            while i < len(s):
                if s[i].isdigit():
                    number += s[i]
                    i += 1
                    continue

                elif s[i] == ",":
                    i += 1
                    break

                else:
                    raise SyntaxError("deserialization of selector string failed -> bad syntax")

        else :
            raise SyntaxError("deserialization of selector string failed -> bad syntax")

    return selector


if __name__ == "__main__":

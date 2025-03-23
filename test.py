# import json
# with open("./test.txt", 'w') as f:
#     # value = ('the answer', 42)
#     # s = str(value)  # convert the tuple to string
#     print(f.write(s))

#     x = [1, 'simple', 'list']
#     json.dumps(x)
#     json.dump(x, f)

import array

item = 1748

"{:8b}".format(25)
format(item, "08b")


def trans(num):
    # bit_str = format(num, "8b")
    out = array.array("B")
    # f"{num:b}"
    is_end_byte = True
    while num > 0:
        to_encode = num % 128
        num = num // 128
        to_encode = f"{to_encode:07b}"
        if is_end_byte:
            out.insert(0, int(f"0{to_encode}",base=2)) # 需要7位对齐
            is_end_byte = False
        else:
            out.insert(0, int(f"1{to_encode}",base=2)) 
    return out

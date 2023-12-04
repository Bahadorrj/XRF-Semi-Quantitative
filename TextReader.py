def get_string(input_file_name):
    s = ""
    with open(input_file_name, 'r') as f:
        line = f.readline()
        while line:
            s = s + line.rstrip()
            line = f.readline()
    return s


def list_items(input_file_name, rng, list_type=str):
    my_list = []
    index = 0
    with open(input_file_name, 'r') as f:
        line = f.readline()
        while line:
            if rng[0] <= index <= rng[1]:
                my_list.append(line.strip())
            line = f.readline()
            index = index + 1
    f.close()
    if list_type == str:
        return my_list
    else:
        return list(map(list_type, my_list))


def condition_dictionary(input_file_name):
    with open(input_file_name, 'r') as f:
        my_dict = {}
        line = f.readline()  # read line
        index = 0
        while line:
            if 'Condition' in line:
                condition = line.strip()
            elif 'Environment' in line:
                start = index + 1
                stop = index + 2048
                my_dict[condition] = {
                    'range': [start, stop],
                    'active': False
                }
            line = f.readline()
            index += 1
    f.close()
    return my_dict


def write_items(output_file_name, preferred_list):
    with open(output_file_name, 'w') as f:
        for i in preferred_list:
            f.write(f"{str(i)}\n")
    f.close()

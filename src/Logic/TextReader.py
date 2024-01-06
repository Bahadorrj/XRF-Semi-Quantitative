from src.Types.ConditionClass import Condition


def set_counts(sample_file) -> None:
    with open(sample_file.get_path(), 'r') as file:
        line = file.readline()  # read line
        index = 0
        condition_pos = -1
        while line:
            if "Condition" in line:
                index = 0
                condition_pos += 1
                c = Condition(line.strip())
                sample_file.get_conditions().append(c)
            try:
                count = int(line.strip())
                sample_file.get_conditions()[condition_pos].get_counts()[
                    index] = count
                index += 1
            except ValueError:
                pass
            line = file.readline()

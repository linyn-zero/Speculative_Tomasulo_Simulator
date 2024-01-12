class Instruction:
    def __init__(self, instruction):
        parts = instruction.split()
        self.op = parts[0]
        self.destination = parts[1]
        self.source1 = parts[2]
        self.source2 = parts[3]
        if self.op == 'ADDD' or 'SUBD':

        elif self.op == 'MULTD' or 'DIVD':

        elif self.op == 'LD' or 'SD':

    def display(self):
        print(self.op, + )
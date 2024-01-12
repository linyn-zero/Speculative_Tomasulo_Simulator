
ROB_MAX_SIZE = 6

def fmc(s, width):
    return '{0:^{width}}'.format(s, width)
def fml(s, width):
    return '{0:<{width}}'.format(s, width)

class ReorderBufferEntry:
    def __init__(self, number, busy=False, instruction=None, state=None, destination=None, value=None, ready=False):
        self.number = number
        self.busy = busy
        self.instruction = instruction  # 操作类型，如ADDD F6 F8 F2
        self.state = state  # 结果是否就绪
        self.destination = destination  # 目标寄存器
        self.value = value  # 计算结果或加载的值
        self.ready = ready  # 结果是否就绪

    def display(self):
        print(fmc(str(self.number),5)+"  "
              + ('Yes' if self.busy else 'No') + '\t '
              + fmc(self.instruction,14) + '  '
              + fml(self.state, 8)
              + fml(self.destination, 6)
              + self.value)

class ReorderBuffer:
    def __init__(self):
        self.queue = Queue(ROB_MAX_SIZE)

    def put(self, instruction):
        if self.queue.isfull():
            print("ROB满了，暂时不加")
            return
        self.queue.push(ReorderBufferEntry())

    def display(self):
        print("\033[1;33mReservation Stations\033[0m")
        print("\033[32mEntry  Busy  Instruction\t\tState   Dest  Value\033[0m")
        for number, entry in enumerate(self.queue):
            entry.display()
        print()

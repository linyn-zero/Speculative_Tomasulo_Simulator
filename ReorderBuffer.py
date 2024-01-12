

def fmc(s, width):
    return ' ' * width if s is None else\
        '{0:^{width}}'.format(str(s), width=width)
def fml(s, width):
    return ' ' * width if s is None else\
        '{0:<{width}}'.format(str(s), width=width)

class ReorderBufferEntry:
    def __init__(self, number, busy=False, instruction=None, state=None, destination=None, value=None, ready=False):
        self.number = number
        self.busy = busy
        self.instruction = instruction  # 操作类型，如ADDD F6 F8 F2
        self.state = state  # 结果是否就绪
        self.destination = destination  # 目标寄存器
        self.value = value  # 计算结果或加载的值
        self.ready = ready  # 结果是否就绪

    def set(self, instruction):
        #新的指令进来了，彻底刷新ROB表项
        self.state = 'Issue'
        self.busy = True
        self.instruction = instruction
        self.destination = instruction.split()[1]
        self.value = None

    def display(self):
        print(fmc(self.number,5)+'  '
                , ('Yes' if self.busy else 'No') + '\t'
                , fml(self.instruction,15)
                , fml(self.state, 8)
                , fml(self.destination, 6)
                , fmc(self.value,5))


class ReorderBuffer:
    def __init__(self, maxlen):
        self.queue = []
        self.maxlen = maxlen
        self.head = 0
        self.tear = 0
        self.size = 0
        for i in range(self.maxlen):
            self.queue.append(ReorderBufferEntry(i+1))

    def push(self, instruction):
        if self.isfull():
            print("ROBQueue is full, and function \'push\' is failed: ")
            print(instruction)
            return
        self.queue[self.tear].set(instruction) # 更新ROB项
        self.size += 1
        self.tear = (self.tear+1) % self.maxlen

    def pop(self):
        if self.isempty():
            print("ROBQueue is empty, and function \'pop\' is failed! ")
            return
        item = self.queue[self.head] #要丢掉了，不用更新
        self.size -= 1
        self.head = (self.head+1) % self.maxlen
        return item

    def isfull(self):
        return self.size == self.maxlen

    def isempty(self):
        return self.size == 0


    def display(self): # 作为ROB的display
        print("\033[1;33mReservation Stations\033[0m")
        print("\033[32mEntry  Busy  Instruction\t State   Dest  Value\033[0m")
        for number, entry in enumerate(self.queue):
            entry.display()
        print(f"\033[3;34mHead={self.head+1} Tear={self.tear+1}\033[0m")
        if self.tear == self.head:
            if self.isfull():
                print("\033[3;34mReorder Buffer is Full.\033[0m")
            else:
                print("\033[3;34mReorder Buffer is Empty.\033[0m")
        print()

    # 作为queue的display
    # def display(self):
    #     head = self.head
    #     tear = self.tear
    #     while not self.isempty():
    #         self.queue[head].display()
    #         head = (head+1) % self.maxlen
    #         if head == tear or self.isempty():
    #             return
    #         # item.display()

#检查输出
from FPOPqueue import FPOPqueue
fq = FPOPqueue()
fq.input('./input1.txt')
fq.display()
rob = ReorderBuffer(4)
while True:
    ins = fq.pop()
    rob.push(ins)
    rob.display()

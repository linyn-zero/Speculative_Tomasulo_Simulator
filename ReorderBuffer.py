
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

    def issue(self, instruction):
        #新的指令进来了，彻底刷新ROB表项
        self.busy = True
        self.instruction = instruction
        self.state = 'Issue'
        op = instruction.split()[0]  # 只有 SD 指令不写寄存器
        self.destination = instruction.split()[1] if op != 'SD' else None
        self.value = None  #会在main.issue更新

    def display(self):
        op = self.instruction.split()[0] if self.instruction is not None else None
        print(fmc(self.number,5)+' '
                , (' Yes' if self.busy else ' No ') +' '
                , fml(self.instruction,14) + ' '
                , fml(self.state, 7)
                , fmc(self.destination, 4) +' '
                , ('' if op=='SD' else self.value if self.state=='Commit'or self.state=='Write' else ''))




class ReorderBuffer:
    def __init__(self):
        self.queue = []
        self.maxlen = ROB_MAX_SIZE
        self.head = 0
        self.tear = 0
        self.size = 0
        for i in range(self.maxlen):
            self.queue.append(ReorderBufferEntry(i+1)) #number是ROBEntry的唯一标识

    def issue(self, instruction): #实现是push（插入队列）
        if self.isfull():
            print(f"ROBQueue is full, and function \'issue {instruction}\' is failed: ")
            return
        number = self.tear + 1 #获取ROB表项序号（逻辑序号，比真实序号大一）
        self.queue[self.tear].issue(instruction) # 更新ROB项
        self.size += 1
        self.tear = (self.tear+1) % self.maxlen
        return number

    def commit(self,ROBEntryNumber): #ROBEntry从write到commit，not busy
        ROBEntry = self.queue[self.head]
        if ((ROBEntryNumber-1+self.maxlen)%self.maxlen == self.head
                and ROBEntry.busy and ROBEntry.state=='Write'):
            ROBEntry.busy=False
            self.pop()
            return True
        return False

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

    def getROBEntry(self, ROBEntryNumber):
        return self.queue[ROBEntryNumber-1]
    def getInstructionList(self):
        instructionList = {}
        head = self.head
        size = self.size
        while size != 0:
            instruction = self.queue[head].instruction
            number = self.queue[head].number
            instructionList[instruction] = number
            head = (head+1) % self.maxlen
            size -= 1
        return instructionList

    def checkRAW(self, beginNumber, keyReg): #在ROB中检查raw冲突
        checkPointer = beginNumber-2 #从目标条目的上一个条目开始检查
        size = self.size - 1
        while size != 0: #向上搜索仍未提交的指令
            if self.queue[checkPointer].destination == keyReg:  #某条目的指令满足 Dest==KeyReg 说明冲突
                state = self.queue[checkPointer].state
                if state=='Exec' or state=='Issue':   #该条目状态为Exec或Issue，需要等待结果
                    return None, checkPointer+1   #返回冲突的ROB条目序号
                elif state=='write':    #该条目的状态为write，可以旁路
                    return self.queue[checkPointer].value, checkPointer+1 #旁路返回ROBEntry的value值（value值的表示工作交给写入时进行）
                # else:           #该条目状态为commit（这种情况只在旧指令刚离开Write状态时发生。状态为commit的指令不会在栈中）
                    # print('真奇怪，出现了状态为 commit 的ROBEntry')

            checkPointer = (checkPointer-1+self.maxlen) % self.maxlen
            size -= 1
        return f'Regs[{keyReg}]', keyReg

    def display(self): # 作为ROB的display
        print("\033[1;33mReorder Buffer\033[0m"
              +(("(\033[3;34mFull\033[0m)" if self.isfull() else "(\033[3;34mEmpty\033[0m)") if self.tear == self.head else '')
              + f": \033[3;34mHead={self.head+1} Tear={self.tear+1}\033[0m")
        print("\033[32mEntry  Busy  Instruction\t State   Dest  Value\033[0m")
        for number, entry in enumerate(self.queue):
            entry.display()


ROB_MAX_SIZE = 6
REORDER_BUFFER = ReorderBuffer()

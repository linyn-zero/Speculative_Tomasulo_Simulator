from FPOPqueue import FQ_OP_QUEUE
from RegisterResultStatus import REGISTER_RESULT_STATUS
from ReorderBuffer import REORDER_BUFFER
from ReservationStations import RESERVATION_STATIONS

def fmc(s, width):
    return ' ' * width if s is None else\
        '{0:^{width}}'.format(str(s), width=width)
def fml(s, width):
    return ' ' * width if s is None else\
        '{0:<{width}}'.format(str(s), width=width)

FILE_PATH = './script.txt'
STD_OP = ['ADDD', 'SUBD', 'MULTD', 'DIVD', 'LD', 'SD']
EXEC_SPEND_CYCLE = {
    'ADDD': 2,
    'SUBD': 2,
    'MULTD': 10,
    'DIVD': 20,
    'LD': 2,
    'SD': 2
}

class RunningCycleTable:
    def __init__(self):
        self.instructionInfo = {}  #存储已发送的指令的状态,ROBEntry,RSEntry
        self.instructionCycle = {}  #存储已发送指令进入各个状态的cycle


    def append(self, instruction, cycle, ROBEntryNumber, RSEntryName):
        self.instructionInfo[instruction] = {'ROBEntry': ROBEntryNumber, 'RSEntry': RSEntryName}
        self.instructionCycle[instruction] = {'Issue': cycle, 'Exec': None, 'Write': None, 'Commit': None}

    def clear(self):
        self.instructionInfo = {}
        self.instructionCycle = {}

    def display(self):
        print("\033[1;33mInstructions Cycle Table\033[0m")
        print("\033[32m\t\t\t\tIssue  Exec  Write  Commit\033[0m")
        for i, (instruction, cycleInfo) in enumerate(self.instructionCycle.items()):
            print(fml(instruction, 14) + ' '
                  , fmc(cycleInfo['Issue'], 5) + ' '
                  , fmc(cycleInfo['Exec'], 4) + ' '
                  , fmc(cycleInfo['Write'], 5) + ' '
                  , fmc(cycleInfo['Commit'], 6))
        print('\033[3;34m注：这张 Cycle Table 展示的是指令进入某一状态的时间。\n'
                        '本程序支持：\n'
                        '   1. Write 阶段的结果旁路到 Exec 阶段\n'
                        '   2. Commit 阶段的写寄存器旁路到 Issue 阶段，使能 RSEntry.ready，以解决 RAW 冲突\n'
                        '   3. 单周期只能发射至多一条指令（多发射也不难实现）\n'
                        '   4. 单周期允许提交至少一条指令（这才叫超标量处理器嘛）\033[0m')

    def setExec(self, instruction, cycle):
        self.instructionCycle[instruction]['Exec'] = cycle
    def setWrite(self, instruction, cycle):
        self.instructionCycle[instruction]['Write'] = cycle
    def setCommit(self, instruction, cycle):
        self.instructionCycle[instruction]['Commit'] = cycle

class SpeculativeTomasulo:
    def __init__(self):
        self.Units = {  # EX阶段的运算单元
            "Add":  False,
            "Mult": False,
            "Mem":  False,
        }
        self.RunningCycle = RunningCycleTable()
        self.cycle = 0

    def issue(self):
        # FP OP Queue 发送 ins 给 ROB 和 RS 。需要ROB和RS都有空位 （每周期只发一条）。
        # 从 FP queue 获取一条指令试试水
        if FQ_OP_QUEUE.isempty():
            return
        instruction = FQ_OP_QUEUE.queue.queue[0]
        op = instruction.split()[0]
        if not REORDER_BUFFER.isfull() and not RESERVATION_STATIONS.isfull(op):
            FQ_OP_QUEUE.pop()  #从 FP queue 中取出
            ROBEntryNumber = REORDER_BUFFER.issue(instruction)  #发射到ROB。ROBEntry状态初始化为issue。（隐式修改RRSmap）
            RSEntryName = RESERVATION_STATIONS.issue(instruction, ROBEntryNumber, REORDER_BUFFER) #发射到RS。RS会有状态更新。
            destination = instruction.split()[1]
            REGISTER_RESULT_STATUS.map(destination, ROBEntryNumber)  # 显式修改RRS映射状态
            self.issueSetValue(ROBEntryNumber,RSEntryName)  #ROB利用RS表项，提前提前提前计算出value的表达式
            self.RunningCycle.append(instruction, self.cycle, ROBEntryNumber, RSEntryName) #加入到列表中
        else:
            print("ROB or RS is full, function \'Issue\' failed. ")

    def issueSetValue(self, ROBEntryNumber, RSEntryName):  #ROB利用RS表项，提前提前提前计算出value的表达式
        ROBEntry = REORDER_BUFFER.getROBEntry(ROBEntryNumber)
        RSEntry = RESERVATION_STATIONS.getRSEntry(RSEntryName)
        outcome = RSEntry.getROBValue()
        ROBEntry.value = outcome

    def exec(self, instruction, instructionInfo): #为单条指令检查ready，为真则将指令状态置为Exec，设置计时器
        RSEntry = RESERVATION_STATIONS.getRSEntry(instructionInfo['RSEntry'])
        ROBEntry = REORDER_BUFFER.getROBEntry(instructionInfo['ROBEntry'])
        op = RSEntry.operation
        if RSEntry.ready:  #检查ready，为真则将指令状态置为Exec，设置计时器，更新CycleTable
            ROBEntry.state = 'Exec'
            RSEntry.timer = EXEC_SPEND_CYCLE[op]-1
            self.RunningCycle.setExec(instruction, self.cycle)


    def write(self,  instruction, instructionInfo):
        #若执行计数器未执行完，更新计数器，保持state=Exec
        RSEntry = RESERVATION_STATIONS.getRSEntry(instructionInfo['RSEntry'])
        if RSEntry.timer >= 0:
            RSEntry.timer -= 1
        # 否则清除RS、修改ROB状态、执行旁路
        if RSEntry.timer < 0:
            op = RSEntry.operation
            RSEntry.clear()
            ROBEntryNumber = instructionInfo['ROBEntry']
            ROBEntry = REORDER_BUFFER.getROBEntry(ROBEntryNumber)
            if op == 'SD':
                a=1 #bubble
            else:
                ROBEntry.state = 'Write' #修改ROB状态
                self.RunningCycle.setWrite(instruction, self.cycle) #更新CycleTable
                #旁路：从ROBEntry.value旁路到RS.v==None的项：遍历RS，找到RS.v==None的RSEntry，根据RS.q找到目标ROBEntry.value
                RESERVATION_STATIONS.forwarding(ROBEntryNumber, ROBEntry.value)


    def commit(self,instruction, instructionInfo):
        op = instruction.split()[0]
        destination = instruction.split()[1]
        if op == 'SD':  #将执行结果写入Memory（do nothing）
            REORDER_BUFFER.commit(instructionInfo['ROBEntry']) #清除ROB（修改state、busy）
        else: #普通指令。清除ROB（修改state、busy）
            if REORDER_BUFFER.commit(instructionInfo['ROBEntry']): # 检查是否为最旧的指令
                self.RunningCycle.setCommit(instruction, self.cycle)
                REGISTER_RESULT_STATUS.unmap(destination)  #将执行结果写入寄存器(清除RRS)

    def init(self, file_path):
        #读入指令
        FQ_OP_QUEUE.input(file_path)
        #初始化 RunningCycle 记录表
        self.RunningCycle.clear()

    #每个周期执行四个操作
    def run(self, file_path):
        self.init(file_path)
        self.cycle = 0
        while True:
            self.display(self.cycle)
            self.cycle += 1
            #对每条指令状态进行判断顺序:提交->写回->执行。RAW只会影响更新的指令，因此从旧往新更新即可。
            for i, (instruction, instructionInfo) in enumerate(self.RunningCycle.instructionInfo.items()):
                ROBEntryNumber = self.RunningCycle.instructionInfo[instruction]['ROBEntry']
                state = REORDER_BUFFER.getROBEntry(ROBEntryNumber).state
                if state == 'Commit':
                    continue  #提交的指令已经完成
                elif state == 'Write':
                    self.commit(instruction, instructionInfo) #最旧指令提交，更新寄存器
                elif state == 'Exec':
                    self.write(instruction, instructionInfo) #可能是对指令Timer--,也可能是将指令write，旁路，更新依赖项ready
                elif state == 'Issue':
                    self.exec(instruction, instructionInfo) #检查ready，为真则将指令状态置为Exec，设置计时器
            self.issue() #这是每个周期都要做的事情
            #终止判断
            if (FQ_OP_QUEUE.isempty()
                    and REORDER_BUFFER.isempty()
                    and RESERVATION_STATIONS.isempty()
                    and REGISTER_RESULT_STATUS.isempty()):
                break
        #打印最后的 RunningCycle 表
        self.display(self.cycle)
        self.RunningCycle.display()
        print("===================================================================================================")


    def display(self, cycle):
        print("===================================================================================================")
        print(f"\033[1;33mCycles {cycle}\033[0m")
        REORDER_BUFFER.display()
        RESERVATION_STATIONS.display()
        REGISTER_RESULT_STATUS.display()
        print("===================================================================================================")

if __name__ == "__main__":
    speculative_tomasulo = SpeculativeTomasulo()
    speculative_tomasulo.run(FILE_PATH)
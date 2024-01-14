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

INPUT_FILE_PATH = './input2.txt'
OUTPUT_FILE_PATH = './output2.txt'
STD_OP = ['ADDD', 'SUBD', 'MULTD', 'DIVD', 'LD', 'SD']
EXEC_SPEND_CYCLE = {
    'ADDD': 2,
    'SUBD': 2,
    'MULTD': 10,
    'DIVD': 20,
    'LD': 2,
    'SD': 1  #SD指令的Exec阶段只计算addr。write阶段检查ready（RAW），满足则写内存。
}

class RunningCycleTable:
    def __init__(self):
        self.instructionInfo = {}  #存储已发送的指令的状态,ROBEntry,RSEntry
        self.instructionCycle = {}  #存储已发送指令进入各个状态的cycle


    def append(self, instructionNumber, instruction, cycle, ROBEntryNumber, RSEntryName):
        self.instructionInfo[instructionNumber] = {'Instruction': instruction, 'State': 'Issue', 'ROBEntry': ROBEntryNumber, 'RSEntry': RSEntryName}
        self.instructionCycle[instructionNumber] = {'Issue': cycle, 'Exec': None, 'Write': None, 'Commit': None}

    def clear(self):
        self.instructionInfo = {}
        self.instructionCycle = {}

    def display(self):
        print("\033[1;33mInstructions Cycle Table\033[0m")
        print("\033[32m\t\t\t\tIssue  Exec  Write  Commit\033[0m")
        for i, (instructionNumber, cycleInfo) in enumerate(self.instructionCycle.items()):
            print(fml(self.instructionInfo[instructionNumber]['Instruction'], 14) + ' '
                  , fmc(cycleInfo['Issue'], 5) + ' '
                  , fmc(cycleInfo['Exec'], 4) + ' '
                  , fmc(cycleInfo['Write'], 5) + ' '
                  , fmc(cycleInfo['Commit'], 6))
        print('\033[3;34m注：这张 Cycle Table 展示的是指令进入某一状态的时间。\n'
                        '本程序支持：\n'
                        '   1. Write 阶段的结果旁路到 Exec 阶段\n'
                        '   2. Commit 阶段的写寄存器旁路到 Issue 阶段，使能 RSEntry.ready，以解决 RAW 冲突\n'
                        '   3. 单周期只能发射至多一条指令（多发射也不难实现）\n'
                        '   4. 单周期允许提交至少一条指令（这才叫超标量处理器嘛）\n'
                        '   5. 互斥访问运算单元与内存（这是容易遗漏的）\033[0m')

    def setExec(self, instructionNumber, cycle):
        self.instructionCycle[instructionNumber]['Exec'] = cycle
        self.instructionInfo[instructionNumber]['State'] = 'Exec'
    def setWrite(self, instructionNumber, cycle):
        self.instructionCycle[instructionNumber]['Write'] = cycle
        self.instructionInfo[instructionNumber]['State'] = 'Write'

    def setCommit(self, instructionNumber, cycle):
        self.instructionCycle[instructionNumber]['Commit'] = cycle
        self.instructionInfo[instructionNumber]['State'] = 'Commit'


class SpeculativeTomasulo:
    def __init__(self):
        self.Units = {  # EX阶段的运算单元
            "Add":  False,
            "Mult": False,
            "Mem":  {'LD': 0, 'SD': False} #值为'LD'或'SD'。LD共享锁，SD互斥锁
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
            instructionNumber = FQ_OP_QUEUE.pop()  #从 FP queue 中取出
            ROBEntryNumber = REORDER_BUFFER.issue(instruction)  #发射到ROB。ROBEntry状态初始化为issue。（隐式修改RRSmap）
            RSEntryName = RESERVATION_STATIONS.issue(instruction, ROBEntryNumber, REORDER_BUFFER) #发射到RS。RS会有状态更新。
            destination = instruction.split()[1]
            self.issueSetValue(ROBEntryNumber,RSEntryName)  #ROB利用RS表项，提前提前提前计算出value的表达式
            self.RunningCycle.append(instructionNumber, instruction, self.cycle, ROBEntryNumber, RSEntryName) #加入到列表中
        else:
            print(f"ROB or RS is full, function \'Issue {instruction}\' failed. ")

    def issueSetValue(self, ROBEntryNumber, RSEntryName):  #ROB利用RS表项，提前提前提前计算出value的表达式
        ROBEntry = REORDER_BUFFER.getROBEntry(ROBEntryNumber)
        RSEntry = RESERVATION_STATIONS.getRSEntry(RSEntryName)
        outcome = RSEntry.getROBValue()
        ROBEntry.value = outcome

    def exec(self, instructionNumber, instructionInfo): #为单条指令检查ready，为真则将指令状态置为Exec，设置计时器
        RSEntry = RESERVATION_STATIONS.getRSEntry(instructionInfo['RSEntry'])
        op = RSEntry.operation
        if (op=='SD'   #SD不需要等待执行ready，直接计算地址
            or RSEntry.ready  #检查ready，为真则将指令状态置为Exec，设置计时器，更新CycleTable
                and (((op=='ADDD'or op=='SUBD') and not self.Units['Add'])  # 运算单元的监听
                    or ((op=='MULTD'or op=='DIVD') and not self.Units['Mult'])
                    or (op=='LD' and not self.Units['Mem']['SD']))):
            if op=='ADDD'or op=='SUBD':  #运算单元的获取
                self.Units['Add'] = True
            elif op=='MULTD'or op=='DIVD':
                self.Units['Mult'] = True
            elif op=='LD':
                self.Units['Mem']['LD'] += 1
            ROBEntry = REORDER_BUFFER.getROBEntry(instructionInfo['ROBEntry'])
            ROBEntry.state = 'Exec'
            op = RSEntry.operation
            RSEntry.timer = EXEC_SPEND_CYCLE[op]-1
            self.RunningCycle.setExec(instructionNumber, self.cycle)


    def write(self,  instructionNumber, instructionInfo):
        #若执行计数器未执行完，更新计数器，保持state=Exec
        RSEntry = RESERVATION_STATIONS.getRSEntry(instructionInfo['RSEntry'])
        if RSEntry.timer >= 0:
            RSEntry.timer -= 1
        # 否则清除RS、修改ROB状态、执行旁路
        if RSEntry.timer < 0:
            op = RSEntry.operation
            ROBEntryNumber = instructionInfo['ROBEntry']
            ROBEntry = REORDER_BUFFER.getROBEntry(ROBEntryNumber)
            if op == 'SD':  #SD不写寄存器。判断写内存条件。不清空RSEntry（commit才清空）
                if RSEntry.ready and self.Units['Mem']['LD']==0 and not self.Units['Mem']['SD']:  # MEM的互斥访问
                    RSEntry.timer = EXEC_SPEND_CYCLE[op] - 1 #访问 Mem 也要 1 cycle
                    self.Units['Mem']['SD'] = True
                    self.RunningCycle.setWrite(instructionNumber, self.cycle)
                    ROBEntry.state = 'Write' #修改ROB状态为Write。SD在Write阶段写内存（脏写，可旁路（未实现）。commit才正式写入内存）
            else:
                if op == 'ADDD' or op == 'SUBD':  # 运算单元的释放
                    self.Units['Add'] = False
                elif op == 'MULTD' or op == 'DIVD':
                    self.Units['Mult'] = False
                elif op == 'LD':
                    self.Units['Mem']['LD'] -= 1
                RSEntry.clear()
                ROBEntry.state = 'Write' #修改ROB状态
                self.RunningCycle.setWrite(instructionNumber, self.cycle) #更新CycleTable
                #旁路：从ROBEntry.value旁路到RS.v==None的项：遍历RS，找到RS.v==None的RSEntry，根据RS.q找到目标ROBEntry.value
                RESERVATION_STATIONS.forwarding(ROBEntryNumber, ROBEntry.value)


    def commit(self,instructionNumber, instructionInfo):
        instruction = instructionInfo['Instruction']
        op = instruction.split()[0]
        destination = instruction.split()[1]
        if op == 'SD':  #将执行结果写入Memory（do nothing）
            self.Units['Mem']['SD'] = False # MEM的释放
            RSEntry = RESERVATION_STATIONS.getRSEntry(instructionInfo['RSEntry'])
            RSEntry.clear()
        #所有指令。清除ROB（修改state、busy）
        if REORDER_BUFFER.commit(instructionInfo['ROBEntry']): # 检查是否为最旧的指令。清除ROB（修改state、busy）
            ROBEntry = REORDER_BUFFER.getROBEntry(instructionInfo['ROBEntry'])
            ROBEntry.state = 'Commit'
            self.RunningCycle.setCommit(instructionNumber, self.cycle)

    def init(self, file_path):
        FQ_OP_QUEUE.input(file_path)  #读入指令
        self.RunningCycle.clear()  #初始化 RunningCycle 记录表

    #每个周期执行四个操作
    def run(self, file_path):
        self.init(file_path)
        self.cycle = 0
        while True:
            self.display(self.cycle)
            if self.cycle==26:
                print()
            self.cycle += 1
            #对每条指令状态进行判断顺序:提交->写回->执行。RAW只会影响更新的指令，因此从旧往新更新即可。
            for i, (instructionNumber, instructionInfo) in enumerate(self.RunningCycle.instructionInfo.items()):
                state = instructionInfo['State']
                if state == 'Commit':
                    continue  #提交的指令已经完成
                elif state == 'Write':
                    self.commit(instructionNumber, instructionInfo) #最旧指令提交，更新寄存器
                elif state == 'Exec':
                    self.write(instructionNumber, instructionInfo) #可能是对指令Timer--,也可能是将指令write，旁路，更新依赖项ready
                elif state == 'Issue':
                    if instructionNumber==5 and self.cycle == 27:
                        print()
                    self.exec(instructionNumber, instructionInfo) #检查ready，为真则将指令状态置为Exec，设置计时器
            self.issue() #这是每个周期都要做的事情
            self.updateRRS()
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

    def updateRRS(self):
        REGISTER_RESULT_STATUS.clear()
        for i, (instructionNumber, instructionInfo) in enumerate(self.RunningCycle.instructionInfo.items()):
            instruction = instructionInfo['Instruction']
            op = instruction.split()[0]
            destination = instruction.split()[1]
            state = instructionInfo['State']
            if op != 'SD' and state != 'Commit':  #只有 SD 指令不写寄存器
                ROBEntryNumber = instructionInfo['ROBEntry']
                REGISTER_RESULT_STATUS.map(destination, ROBEntryNumber)


    def display(self, cycle):
        print("===================================================================================================")
        print(f"\033[1;33mCycles {cycle}\033[0m")
        REORDER_BUFFER.display()
        RESERVATION_STATIONS.display()
        REGISTER_RESULT_STATUS.display()
        print("===================================================================================================")

if __name__ == "__main__":
    speculative_tomasulo = SpeculativeTomasulo()
    speculative_tomasulo.run(INPUT_FILE_PATH)
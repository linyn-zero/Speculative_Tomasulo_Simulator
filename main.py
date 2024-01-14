from FPOPqueue import FQ_OP_QUEUE
from RegisterResultStatus import REGISTER_RESULT_STATUS
from ReorderBuffer import REORDER_BUFFER
from ReservationStations import RESERVATION_STATIONS

FILE_PATH = './input1.txt'
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
        self.instructionInfo[instruction] = {'State': 'Issue', 'ROBEntry': ROBEntryNumber, 'RSEntry': RSEntryName}
        self.instructionCycle[instruction] = {'Issue': cycle, 'Exec': None, 'Write': None, 'Commit': None}

    def clear(self):
        self.instructionInfo = {}
        self.instructionCycle = {}

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

    def issueSetValue(self, ROBEntryNumber, RSEntryName):
        ROBEntry = REORDER_BUFFER.getROBEntry(ROBEntryNumber)
        RSEntry = RESERVATION_STATIONS.getRSEntry(RSEntryName)
        outcome = RSEntry.getROBValue()
        ROBEntry.value = outcome

    def exec(self, instructionInfo): #检查ready，为真则将指令状态置为Exec，设置计时器
        RSEntry = RESERVATION_STATIONS.getRSEntry(instructionInfo['RSEntry'])
        ROBEntry = REORDER_BUFFER.getROBEntry(instructionInfo['ROBEntry'])
        op = RSEntry.operation
        if RSEntry.ready:
            ROBEntry.state = 'Exec'
            RSEntry.timer = EXEC_SPEND_CYCLE[op]


    def write(self,instruction, instructionInfo):
        #若执行计数器未执行完，更新计数器，保持state=Exec
        RSEntry = RESERVATION_STATIONS.getRSEntry(instructionInfo[instruction]['Name'])
        if RSEntry.timer != 0:
            RSEntry.timer -= 1
        # 否则清除RS、修改ROB状态、执行旁路
        else:
            RSEntry.clear()
            op = instruction.split()[0]
            ROBEntryNumber = instructionInfo[instruction]['ROBEntryNumber']
            ROBEntry = REORDER_BUFFER.getROBEntry(ROBEntryNumber)
            if op == 'SD':
                a=1#bubble
            else:
                ROBEntry.state = 'Write' #修改ROB状态
                #旁路：从ROBEntry.value旁路到RS.v==None的项：遍历RS，找到RS.v==None的RSEntry，根据RS.q找到目标ROBEntry.value
                RESERVATION_STATIONS.forwarding(ROBEntryNumber, ROBEntry.value)


    def commit(self,instruction, instructionInfo):
        op = instruction.split()[0]
        destination = instruction.split()[1]
        if op == 'SD':  #将执行结果写入Memory（do nothing）
            REORDER_BUFFER.commit(instructionInfo[instruction]['ROBEntry']) #清除ROB（修改state、busy）
        else: #普通指令
            if REORDER_BUFFER.commit(instructionInfo[instruction]['ROBEntry']): #清除ROB（修改state、busy）
                REGISTER_RESULT_STATUS.unmap(destination)  #将执行结果写入寄存器(清除RRS)

    def init(self, file_path):
        #读入指令
        FQ_OP_QUEUE.input(file_path)
        #初始化 RunningCycle 记录表
        self.RunningCycle.clear()

    #每个周期执行四个操作
    def run(self, file_path):
        self.init(file_path)
        cycle = 0
        limit = 10
        while limit > 0 :
            self.display(cycle)
            cycle += 1
            limit -= 1
            #对每条指令状态进行判断顺序:提交->写回->执行。RAW只会影响更新的指令，因此从旧往新更新即可。
            for i, (instruction, instructionInfo) in enumerate(self.RunningCycle.instructionInfo.items()):
                state = self.RunningCycle.instructionInfo[instruction]['State']
                if state == 'Commit':
                    continue  #提交的指令已经完成
                elif state == 'Write':
                    self.commit(instruction, instructionInfo) #最旧指令提交，更新寄存器
                elif state == 'Exec':
                    self.write(instruction, instructionInfo) #可能是对指令Timer--,也可能是将指令write，旁路，更新依赖项ready
                elif state == 'Issue':
                    self.exec(instructionInfo) #检查ready，为真则将指令状态置为Exec，设置计时器
            self.issue() #这是每个周期都要做的事情

            # self.exec()  #这是部分指令要做的事情.考虑exec与write/commit的顺序关系.计时器的加减规则
            # self.write() #这是部分指令要做的事情
            # self.commit()#这是部分指令要做的事情

            #终止判断
            if (FQ_OP_QUEUE.isempty()
                    and REORDER_BUFFER.isempty()
                    and RESERVATION_STATIONS.isempty()
                    and REGISTER_RESULT_STATUS.isempty()):
                break

        #打印最后的 RunningCycle 表

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
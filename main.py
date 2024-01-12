from ReorderBuffer import ReorderBuffer
from RegisterResultStatus import RegisterResultStatus
from FPOPqueue import FPOPqueue
from ReservationStations import ReservationStations

FILE_PATH = './input1.txt'
ROB_MAX_SIZE = 6
ADDD_MAX_SIZE = 3
MULT_MAX_SIZE = 2
LD_MAX_SIZE = 2

class SpeculativeTomasulo:
    def __init__(self):
        self.ReorderBuffer = ReorderBuffer(ROB_MAX_SIZE)
        self.ReservationStation = ReservationStations(ADDD_MAX_SIZE, MULT_MAX_SIZE, LD_MAX_SIZE)
        self.RegisterResultStatus = RegisterResultStatus()
        self.FPOPqueue = FPOPqueue()
        self.Units = {  # EX阶段 运算单元
            "Add":  False,
            "Mult": False,
            "Mem":  False,
        }
        # self.RunningCycle = #最后再实现吧

    def issue(self):
        # FP OP Queue 发送 ins 给 ROB （每周期只发一条。令人迷惑的要求）
        if not self.ReorderBuffer.isfull():

        # ROB 发送 ins 给 RS
        if not self.ReservationStation.

    def exec(self):

    def write(self):

    def commit(self):

    def init(self):
        #读入指令
        self.FPOPqueue.input(FILE_PATH)

        #初始化 RunningCycle 记录表
        # self.

    #每个周期执行四个操作
    def run(self):
        cycle = 0
        while True:
            self.display(cycle)
            cycle += 1
            self.issue()
            self.exec()
            self.write()
            self.commit()
            if (self.FPOPqueue.isempty()
                    and self.ReorderBuffer.isempty()
                    and self.ReservationStation.isempty()
                    and self.RegisterResultStatus.isempty()):
                break
        #打印最后的 RunningCycle 表


    def display(self, cycle):
        print("========================================")
        print(f"\033[1;33mCycles {cycle}\033[0m")
        self.ReorderBuffer.display()
        self.ReservationStation.display()
        self.RegisterResultStatus.display()
        print("========================================")

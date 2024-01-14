def fmc(s, width):
    return ' ' * width if s is None else\
        '{0:^{width}}'.format(str(s), width=width)
def fml(s, width):
    return ' ' * width if s is None else\
        '{0:<{width}}'.format(str(s), width=width)

class ReservationStationsEntry:
    def __init__(self, name, time=-1, busy=False, operation=None,
                 value1=None, value2=None, source1=None, source2=None,
                 destination=None, value=None, address=None, ready=False):
        self.name = name    # 初始化后不修改
        self.timer = time   # 只在Ex阶段使用
        self.busy = busy    # 该项是否使用中
        self.operation = operation  # 操作类型，如ADD, Mult
        self.value1 = value1    #Vj
        self.value2 = value2    #Vk
        self.source1 = source1  #Qj。计算outcome时会用到
        self.source2 = source2  #Qk
        self.destination = destination  # 目标寄存器
        self.address = address  #Mem指令的地址
        self.ready = ready  # 结果是否就绪。Qj和Qk都None时，ready！

    def isbusy(self):
        return self.busy

    def updateReady(self):
        self.ready = self.value1 is not None and self.value2 is not None or self.address is not None

    def clear(self):
        self.timer = -1
        self.busy = False
        self.operation = None
        self.value1 = None
        self.value2 = None
        self.source1 = None
        self.source2 = None
        self.destination = None
        self.address = None
        self.ready = False

    def display(self):
        if self.busy:
            print((fmc(self.timer, 4) if self.timer >= 0 else '    ')+' '
                  ,fml(self.name, 5)+'  '
                  ,'Yes '
                  ,fml(self.operation, 5)+ ' '
                  ,(fml(self.value1, 10) if self.value1 is not None else '          ')+ ' '
                  ,(fml(self.value2, 10) if self.value2 is not None else '          ')+ ' '
                  ,('  ' if self.source1 is None or self.value1 is not None else f'#{self.source1}' if isinstance(self.source1, int) else self.source1)+ ' '
                  ,('  ' if self.source2 is None or self.value2 is not None else f'#{self.source2}' if isinstance(self.source2, int) else self.source2)+ ' '
                  ,f' #{self.destination} '+ ' '
                  ,self.address)
        else:
            print('      '+ fml(self.name, 5)+'  '+' No ')

    def issue(self, instruction,ROBEntryNumber, REORDER_BUFFER):  #RSEntry加入一个新条目，更新条目状态
        self.busy = True
        op = instruction.split()[0]
        self.operation = instruction.split()[0]
        #Cal单元
        if op == 'ADDD' or op == 'SUBD'or op == 'MULTD' or op == 'DIVD':
            self.destination = ROBEntryNumber  #结果所在的ROB表项（逻辑序号。根据目的寄存器在RRS的映射得到）
            #检查操作数是否准备好
            src1 = instruction.split()[2]
            src2 = instruction.split()[3]
            #Vj and Qj。操作数为浮点寄存器，检查是否在ROB之前的未commit的条目中。有则等待，直到该条目状态write。没有则代表可以使用
            self.value1, self.source1 = REORDER_BUFFER.checkRAW(self.destination, src1)  #检查ROB中对应条目的过去条目的 Dest 是否与该条目的 src 冲突
            #Vk and Qk#操作数为浮点寄存器，检查是否在ROB之前的未commit的条目中。有则等待，直到该条目状态write。没有则代表可以使用
            self.value2, self.source2 = REORDER_BUFFER.checkRAW(self.destination, src2)  #检查ROB中对应条目的过去条目的 Dest 是否与该条目的 src 冲突
            self.address = None
        #Mem单元
        else:
            ValReg = instruction.split()[1]
            imm = instruction.split()[2]
            AddrReg = instruction.split()[3]
            self.address = f'{imm}+Regs[{AddrReg}]'
            if op == 'LD':  #如果是LD，则设置Dest。
                self.destination = ROBEntryNumber
                self.value1 = None
                self.source1 = None
                self.value2 = None
                self.source2 = None
            elif op=='SD':  #如果是SD，则设置SrcReg
                self.destination = None
                self.value1 = None
                self.source1 = ValReg
                self.value2 = None
                self.source2 = None
        self.updateReady()

    def getROBValue(self):
        op = self.operation
        if op == 'ADDD' or op == 'SUBD'or op == 'MULTD' or op == 'DIVD':
            v1 = '#'+str(self.source1) if isinstance(self.source1, int) else self.source1 #ROBEntryNumber或者浮点寄存器名
            v2 = '#'+str(self.source2) if isinstance(self.source2, int) else self.source2
            if op == 'ADDD':
                return v1+'+'+v2
            if op == 'SUBD':
                return v1+'-'+v2
            if op == 'MULTD':
                return v1+'*'+v2
            if op == 'DIVD':
                return v1+'/'+v2
        else:
            if op == 'LD':
                return f'Mem[{self.name}]'

class Station:
    def __init__(self, maxlen, name):
        self.station = []
        self.maxlen = maxlen
        for i in range(maxlen):
            self.station.append(ReservationStationsEntry(name + str(i + 1)))

    def isfull(self):
        full = True
        for i, entry in enumerate(self.station):
            if not entry.isbusy():
                full = False
        return full

    def isempty(self):
        empty = True
        for i, entry in enumerate(self.station):
            if entry.isbusy():
                empty = False
        return empty

    def issue(self, instruction, ROBEntryNumber, REORDER_BUFFER):
        success = False #防止未经过检查的调用
        for i in range(self.maxlen): # 找到站的空条目，使用它
            if not self.station[i].isbusy():
                success = True
                self.station[i].issue(instruction,ROBEntryNumber, REORDER_BUFFER)  #返回RSEntryName
                return self.station[i].name

        if not success:
            print('This Station is full!! Can\'t add new instruction!!')

    def forwarding(self, ROBEntryNumber, value):
        for i in range(self.maxlen):
            RSEntry = self.station[i]
            if RSEntry.isbusy():
                if RSEntry.value1 is None and RSEntry.source1==ROBEntryNumber:
                    RSEntry.value1 = value
                if RSEntry.value2 is None and RSEntry.source2==ROBEntryNumber:
                    RSEntry.value2 = value
                RSEntry.updateReady()

    def display(self):
        for i, entry in enumerate(self.station):
            entry.display()



class ReservationStations:
    def __init__(self):
        self.AdddStation = Station(ADDD_MAX_SIZE, 'Add')
        self.MultStation = Station(MULT_MAX_SIZE, 'Mult')
        self.LoadStation = Station(LD_MAX_SIZE, 'Load')

    def getRSEntry(self, name):
        if name[:3] == 'Add':
            number = int(name[3:])
            if 0 <= number-1 < self.AdddStation.maxlen:
                return self.AdddStation.station[number-1]
            else:
                print(f'There is\'t RSEntry Add{number}')
        elif name[:4] == 'Mult':
            number = int(name[4:])
            if 0 <= number-1 < self.MultStation.maxlen:
                return self.MultStation.station[number-1]
            else:
                print(f'There is\'t RSEntry Mult{number}')
        elif name[:4] == 'Load':
            number = int(name[4:])
            if 0 <= number-1 < self.LoadStation.maxlen:
                return self.LoadStation.station[number-1]
            else:
                print(f'There is\'t RSEntry Load{number}')

    def getStation(self,op):
        if op=='ADDD'or op=='SUBD':
            return self.AdddStation
        elif op == 'MULTD' or op == 'DIVD':
            return self.MultStation
        elif op == 'LD' or op == 'SD':
            return self.LoadStation

    def forwarding(self, ROBEntryNumber, value):
        self.AdddStation.forwarding(ROBEntryNumber, value)
        self.MultStation.forwarding(ROBEntryNumber, value)
        self.LoadStation.forwarding(ROBEntryNumber, value)


    def isfull(self, op):  # 指定op站为full
        return self.getStation(op).isfull()

    def isempty(self):  #所有RS为空
        return self.AdddStation.isempty() and self.MultStation.isempty() and self.LoadStation.isempty()

    def issue(self, instruction, ROBEntryNumber, REORDER_BUFFER):
        op = instruction.split()[0]
        if not self.isfull(op):  # 对应站非空，即意味着可以加入
            return self.getStation(op).issue(instruction, ROBEntryNumber, REORDER_BUFFER) #返回RSEntryName

    def display(self):
        print("\033[1;33mReservation Stations\033[0m")
        print("\033[32mTime  Name   Busy  Op     Vj          Vk          Qj  Qk  Dest  Addr\033[0m")
        self.AdddStation.display()
        self.MultStation.display()
        self.LoadStation.display()


ADDD_MAX_SIZE = 3
MULT_MAX_SIZE = 2
LD_MAX_SIZE = 2

RESERVATION_STATIONS = ReservationStations()

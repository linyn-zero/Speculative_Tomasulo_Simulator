


class ReservationStationsEntry:
    def __init__(self, name, time=0, busy=False, operation=None,
                 value1=None, value2=None, source1=None, source2=None,
                 destination=None, ready=False):
        self.name = name
        self.time = time
        self.busy = busy
        self.operation = operation  # 操作类型，如ADD, Mult
        self.value1 = value1    #Vj
        self.value2 = value2    #Vk
        self.source1 = source1  #Qj
        self.source2 = source2  #Qk
        self.destination = destination  # 目标寄存器
        self.ready = ready  # 结果是否就绪

    def display(self):
        print("未完成版:", self.time, self.name, self.busy, self.operation, self.value1, self.value1, self.source1, self.source2, self.destination)

class Station:
    def __init__(self, maxlen, name):
        self.station = []
        for i in range(maxlen):
            self.station.append(ReservationStationsEntry(name + str(i + 1)))

    def isfull(self):
        full = True
        for i, entry in enumerate(self.station):
            if not entry.busy:
                full = False
        return full

    def isempty(self):
        empty = True
        for i, entry in enumerate(self.station):
            if entry.busy:
                empty = False
        return empty

    def display(self):
        for i, entry in enumerate(self.station):
            entry.displayStr()
class ReservationStations:
    def __init__(self, ADDD_MAX_SIZE, MULT_MAX_SIZE, LD_MAX_SIZE):
        self.AdddStation = Station(ADDD_MAX_SIZE, 'Add')
        self.MultStation = Station(MULT_MAX_SIZE, 'Mult')
        self.LoadStation = Station(LD_MAX_SIZE, 'Load')

    def isfull(self):
        return self.AdddStation.isfull() and self.LoadStation.isfull() and self.MultStation.isfull()
    def isempty(self):
        return self.AdddStation.isempty() and self.MultStation.isempty() and self.LoadStation.isempty()

    def display(self):
        print("\033[1;33mReservation Stations\033[0m")
        print("\033[32mTime  Name   Busy  Op    Vj                  Vk                  Qj  Qk  Dest  \033[0m")
        self.AdddStation.display()
        self.MultStation.display()
        self.LoadStation.display()
        print()

class RegisterResultStatus:
    def __init__(self, ):
        self.reg_map = {
            "F0": 0,
            "F2": 1,
            "F4": 2,
            "F6": 3,
            "F8": 4,
            "F10": 5
        }
        self.reorder_number = [None, None, None, None, None, None]
        self.busy_status = [False,False,False,False,False,False,]

    def map(self, AReg, ROBEntryNumber):
        reg_number = self.reg_map[AReg]
        self.reorder_number[reg_number] = ROBEntryNumber
        self.busy_status[reg_number] = True

    def unmap(self, archiReg):
        reg_number = self.reg_map[archiReg]
        self.busy_status[reg_number] = False

    def clear(self):
        self.reorder_number = [None, None, None, None, None, None]
        self.busy_status = [False,False,False,False,False,False,]

    def getROBNumber(self, destination):
        item_number = self.reg_map[destination]
        if self.busy_status[item_number]:
            return self.reorder_number[item_number]
        else:
            print(f"这个 Destination 没有 RRS 映射：{destination}")

    def isempty(self):
        empty = True
        for i, busy in enumerate(self.busy_status):
            if busy:
                empty = False
                break
        return empty

    def display(self):
        print("\033[1;33mRegister Result Status\033[0m")
        print("\033[32m\t\t\tF0\tF2\tF4\tF6\tF8\tF10\t\033[0m")
        print("\033[3;33mReorder#   \033[0m", "".join("\033[3;32m#" + str(self.reorder_number[i]) + "\033[0m\t"
                                                    if self.busy_status[i]
                                                    else "\t"
                                                    for i in range(MAX_SIZE)))
        print("\033[33mBusy       \033[0m", "".join("\033[3;32mYes\033[0m\t"
                                                    if self.busy_status[i]
                                                    else "No\t"
                                                    for i in range(MAX_SIZE)))


MAX_SIZE = 6
REGISTER_RESULT_STATUS = RegisterResultStatus()



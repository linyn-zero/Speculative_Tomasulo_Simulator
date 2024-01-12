MAX_SIZE = 6

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
        self.reorder_item = [None,None,None,None,None,None]
        self.busy_status = [False,False,False,False,False,False,]

    def map(self, archiReg, robItem):
        reg_number = self.reg_map[archiReg]
        self.reorder_item[reg_number] = robItem
        self.busy_status[reg_number] = True

    def unmap(self, archiReg):
        reg_number = self.reg_map[archiReg]
        self.busy_status[reg_number] = False

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
        print("\033[3;33mReorder#   \033[0m", "".join("\033[3;32m#"+str(self.reorder_item[i])+"\033[0m\t"
                                                    if self.busy_status[i]
                                                    else "\t"
                                                    for i in range(MAX_SIZE)))
        print("\033[33mBusy       \033[0m", "".join("\033[3;32mYes\033[0m\t"
                                                    if self.busy_status[i]
                                                    else "No\t"
                                                    for i in range(MAX_SIZE)))
        print()

rrs = RegisterResultStatus()
rrs.display()
rrs.map("F4", 5)
rrs.display()
rrs.map("F2", 3)
rrs.display()
rrs.map("F6", 2)
rrs.display()
rrs.unmap("F2")
rrs.display()


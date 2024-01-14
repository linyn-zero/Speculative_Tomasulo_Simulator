from queue import Queue

class FPOPqueue:
    def __init__(self):
        self.queue = Queue()
        self.size = 0

    def push(self, instruction):
        self.queue.put(instruction)

    def pop(self):
        self.queue.get()
        self.size += 1
        return self.size-1

    def isempty(self):
        return self.queue.empty()

    #从文件读入指令队列
    def input(self, file_path):
        try:
            with open(file_path, 'r') as file:
                # 读取文件的每一行作为一个字符串
                lines = file.readlines()

                # 打印每一行字符串
                for line in lines:
                    self.queue.put(line.strip())  # strip() 用于移除行尾的换行符

        except FileNotFoundError:
            print(f"File '{file_path}' not found.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def display(self):
        print("\033[1;33mFP OP Queue\033[0m")
        size = self.queue.qsize()
        for i in range(size):
            instruction = self.queue.get()
            print(instruction)
            self.queue.put(instruction)
        print()


FQ_OP_QUEUE = FPOPqueue()



#读文件检查
# fq = FPOPqueue()
# fq.input('./input1.txt')
# fq.display()

#逻辑检查
# fq = FPOPqueue()
# fq.push("ADD F2 F3 F3")
# fq.display()
# fq.push("MULT F2 F3 F3")
# fq.display()
# fq.push("LD F2 F3 F3")
# fq.display()
# fq.push("SD F2 F3 F3")
# fq.display()
# print("头元素", fq.queue.queue[0])
# fq.display()
# print(fq.pop())
# fq.display()
# print(fq.pop())
# fq.display()
# print(fq.pop())
# fq.display()

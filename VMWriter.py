class VMWriter:
    def __init__(self, output_path):
        self.file = open(output_path, 'w', encoding='UTF-8')

    def write_push(self, segment, index):
        self.file.write(f"push {segment} {index}\n")

    def write_pop(self, segment, index):
        self.file.write(f"pop {segment} {index}\n")

    def write_arithmetic(self, command):
        self.file.write(f"{command}\n")

    def write_label(self, label):
        self.file.write(f"label {label}\n")

    def write_goto(self, label):
        self.file.write(f"goto {label}\n")

    def write_if_goto(self, label):
        self.file.write(f"if-goto {label}\n")

    def write_call(self, name, nArgs):
        self.file.write(f"call {name} {nArgs}\n")

    def write_function(self, name, nVars):
        self.file.write(f"function {name} {nVars}\n")

    def write_return(self):
        self.file.write(f"return\n")

    def write_comment(self, comment):
        self.file.write(f"// {comment}\n")

    def write_empty_line(self):
        self.file.write("\n")

    def close(self):
        self.file.close()

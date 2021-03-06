#!/usr/bin/python


import json

import joint
import functions
import joint_functions
import flag_functions
import flag
import register


class Instruction(object):

    def __init__(self, name, mnemonic, operands, result, function_name, bound):
        self.name = name
        self.mnemonic = mnemonic
        self.operands = operands.split(' ')
        self.result = result
        self.function_name = function_name
        self.joints = {}
        for elem in bound.split(' '):
            self.joints[elem] = joint.Joint(self)

    def __str__(self):
        return self.mnemonic

    def check_correctness(self):
        if self.operands != '-':
            for operand in self.operands:
                if operand not in self.mnemonic:
                    return False
        if self.result != '-' and self.result not in self.mnemonic:
            return False
        return True

    def execute(self, *operands):
        if len(operands) != len(self.operands):
            raise ValueError
        operands_dict = dict(zip(self.operands, operands))
        refined_operands = []
        for op in operands:
            # FIXME: Dirty hack for JMP instructions
            if isinstance(op, register.Register) and self.name != 'JMP':
                refined_operands.append(op.value)
            else:
                refined_operands.append(op)
        result = getattr(functions, self.function_name)(*refined_operands)
        if self.result:
            operands_dict[self.result].value = result
        for joint_name, joint in self.joints.iteritems():
            if isinstance(joint.j_to, flag.Flag):
                joint.bend(
                    joint_functions.set_flag,
                    joint.j_to,
                    getattr(flag_functions, joint.j_to.function),
                    result
                )

    def set_joint(self, joint):
        self.joint = joint


class ArithmeticInstruction(Instruction):

    def __init__(self, name, mnemonic, operands, result, function_name, bound):
        super(ArithmeticInstruction, self).__init__(
            name, mnemonic, operands,
            result, function_name, bound
        )

    def execute(self, *operands):
        if len(operands) != len(self.operands):
            raise ValueError
        operands_dict = dict(zip(self.operands, operands))
        refined_operands = []
        for op in operands:
            if isinstance(op, register.Register):
                refined_operands.append(op.value)
            else:
                refined_operands.append(op)
        result = getattr(functions, self.function_name)(*refined_operands)
        if self.result:
            operands_dict[self.result].value = result
            operands_dict[self.result].fit()
        for joint_name, joint in self.joints.iteritems():
            if isinstance(joint.j_to, flag.Flag):
                joint.bend(
                    joint_functions.set_flag,
                    joint.j_to,
                    getattr(flag_functions, joint.j_to.function),
                    result
                )


class DataTransferInstruction(Instruction):

    def __init__(self, name, mnemonic, operands, result, function_name, bound):
        super(DataTransferInstruction, self).__init__(
            name, mnemonic, operands,
            result, function_name, bound
        )

    def execute(self, *operands):
        if len(operands) != len(self.operands):
            raise ValueError
        size = None
        for operand in operands:
            if isinstance(operand, register.Register):
                size = operand.size
        # Hack - need at least one register
        #if not size:
        #    raise AttributeError
        operands_dict = dict(zip(self.operands, operands))
        getattr(functions, self.function_name)(*operands)
        for joint_name, joint in self.joints.iteritems():
            if isinstance(joint.j_to, flag.Flag):
                joint.bend(
                    joint_functions.set_flag,
                    joint.j_to,
                    getattr(flag_functions, joint.j_to.function),
                    result
                )


class ControlTransferInstruction(Instruction):

    def __init__(self, name, mnemonic, operands, result, function_name, bound):
        super(ControlTransferInstruction, self).__init__(
            name, mnemonic, operands,
            result, function_name, bound
        )

    def execute(self, *operands):
        if len(operands) != len(self.operands):
            raise ValueError
        operands_dict = dict(zip(self.operands, operands))
        getattr(functions, self.function_name)(*operands)
        for joint_name, joint in self.joints.iteritems():
            if isinstance(joint.j_to, flag.Flag):
                joint.bend(
                    joint_functions.set_flag,
                    joint.j_to,
                    getattr(flag_functions, joint.j_to.function),
                    result
                )


def load_from_file(filename):
    inst_file = open(filename)
    inst_str = inst_file.read()
    inst_file.close()
    instructions = json.loads(inst_str)
    result = []
    for instruction in instructions:
        operands = [
            instruction['name'],
            instruction['mnemonic'],
            instruction['operands'],
            instruction['result'],
            instruction['function'],
            instruction['bound']
        ]
        if instruction['type'] == 'arithmetic':
            result.append(ArithmeticInstruction(*operands))
        elif instruction['type'] == 'control_transfer':
            result.append(ControlTransferInstruction(*operands))
        elif instruction['type'] == 'data_transfer':
            result.append(DataTransferInstruction(*operands))
        else:
            result.append(Instruction(*operands))
    return result

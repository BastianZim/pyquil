import math

from syrupy.assertion import SnapshotAssertion

from pyquil import Program
from pyquil.api._compiler import QPUCompiler
from pyquil.gates import RX, MEASURE, RZ
from pyquil.quilatom import FormalArgument
from pyquil.quilbase import DefCalibration


def simple_program():
    program = Program()
    readout = program.declare("ro", "BIT", 3)
    program += MEASURE(0, readout[0])
    return program


def test_compile_with_quilt_calibrations(compiler: QPUCompiler):
    program = simple_program()
    q = FormalArgument("q")
    defn = DefCalibration("H", [], [q], [RZ(math.pi / 2, q), RX(math.pi / 2, q), RZ(math.pi / 2, q)])
    cals = [defn]
    program.inst(cals)
    # this should more or less pass through
    compilation_result = compiler.quil_to_native_quil(program, protoquil=True)
    assert compilation_result.calibrations == cals
    assert program.calibrations == cals
    assert compilation_result == program

def test_transpile_qasm_2(compiler: QPUCompiler, snapshot: SnapshotAssertion):
    qasm = 'OPENQASM 2.0;\nqreg q[3];\ncreg ro[2];\nmeasure q[0] -> ro[0];\nmeasure q[1] -> ro[1];'
    program = compiler.transpile_qasm_2(qasm)
    assert program.out() == snapshot

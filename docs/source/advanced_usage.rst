.. _advanced_usage:

==============
Advanced usage
==============

.. note::

    If you're running locally, remember set up the QVM and quilc in server mode before trying to use
    them: :ref:`server`.

.. _pyquil_configuration:

********************
pyQuil configuration
********************

:py:class:`~pyquil.api.QCSClient` instructs pyQuil on how to connect with the components needed to compile and run
programs (``quilc``, ``qvm``, and QCS). Any APIs that take a configuration object as input
(e.g. :py:func:`~pyquil.api.get_qc`) typically do so optionally, so that a default configuration can be loaded
for you if one is not provided. You can override this default configuration by either instantiating your own
:py:class:`~pyquil.api.QCSClient` object and providing it as input to the function in question,
or by setting the ``QCS_SETTINGS_FILE_PATH`` and/or ``QCS_SECRETS_FILE_PATH`` environment variables to have
pyQuil load its settings and secrets from specific locations. By default, configuration will be loaded from
``$HOME/.qcs/settings.toml`` and ``$HOME/.qcs/secrets.toml``.

Additionally, you can override whichever QVM and quilc URLs are loaded from ``settings.toml``
(``profiles.<profile>.applications.pyquil.qvm_url`` and ``profiles.<profile>.applications.pyquil.quilc_url`` fields)
by setting the ``QCS_SETTINGS_APPLICATIONS_QVM_URL`` and/or ``QCS_SETTINGS_APPLICATIONS_QUILC_URL``
environment variables. If these URLs are missing from ``settings.toml`` and are not set by environment variables,
the following defaults will be used (as they correspond to the default behavior of the QVM and quilc when running
locally):

- QVM URL: ``http://127.0.0.1:5000``
- quilc URL: ``tcp://127.0.0.1:5555``

**************
Multithreading
**************

:py:class:`~pyquil.api.QuantumComputer` objects are safe to share between threads, enabling you to execute and retrieve
results for multiple programs or parameter values at once.  Note that :py:class:`~pyquil.Program` and
:py:class:`~pyquil.api.EncryptedProgram` are **not** thread-safe, and should be copied (with ``copy()``) before use in a
concurrent context.

.. note::
    The QVM processes incoming requests in parallel, while a QPU may process them sequentially or in parallel
    (depending on the qubits used). If you encounter timeouts while trying to run large numbers of programs against a
    QPU, try increasing the ``execution_timeout`` parameter on calls  to :py:func:`~pyquil.get_qc` (specified in
    seconds).

.. note::
    We suggest running jobs with a minimum of 2x parallelism, so that the QVM or QPU
    is fully occupied while your program runs and no time is wasted in between jobs.

.. note::
   Because pyQuil does not currently have an ``asyncio`` API it is recommended to use ``ThreadPool``\s.

Below is an example that demonstrates how to use pyQuil in a multithreading scenario:

.. code:: python

    from multiprocessing.pool import ThreadPool

    from pyquil import get_qc, Program
    from pyquil.api import QCSClient

    qc = get_qc("Aspen-M-3")


    def run(program: Program):
        return qc.run(qc.compile(program)).readout_data.get("ro")


    programs = [
        Program(
            "DECLARE ro BIT",
            "RX(pi) 0",
            "MEASURE 0 ro",
        ).wrap_in_numshots_loop(10),
    ] * 20

    with ThreadPool(5) as pool:
        results = pool.map(run, programs)

    for i, result in enumerate(results):
        print(f"Results for program {i}:\n{result}\n")


*************************
Alternative QPU endpoints
*************************

Rigetti QCS supports alternative endpoints for access to a QPU architecture, useful for very particular cases.
Generally, this is useful to call "mock" or test endpoints, which simulate the results of execution for the
purposes of integration testing without the need for an active reservation or contention with other users.
See the `QCS API Docs <https://docs.api.qcs.rigetti.com/#tag/endpoints>`_ for more information on QPU Endpoints.

To be able to call these endpoints using pyQuil, enter the ``endpoint_id`` of your desired endpoint in one
of the sites where ``quantum_processor_id`` is used:

.. code:: python

    # Option 1
    qc = get_qc("Aspen-M-3", endpoint_id="my_endpoint")

    # Option 2
    qam = QPU(quantum_processor_id="Aspen-M-3", endpoint_id="my_endpoint")

After doing so, for all intents and purposes - compilation, optimization, etc - your program will behave the same
as when using "default" endpoint for a given quantum processor, except that it will be executed by an
alternate QCS service, and the results of execution should not be treated as correct or meaningful.


************************
Using qubit placeholders
************************

.. note::
    The functionality provided inline by ``QubitPlaceholders`` is similar to writing a function which returns a
    ``Program``, with qubit indices taken as arguments to the function.

In pyQuil, we typically use integers to identify qubits

.. testcode:: placeholders

    from pyquil import Program
    from pyquil.gates import CNOT, H
    print(Program(H(0), CNOT(0, 1)))

.. testoutput:: placeholders

    H 0
    CNOT 0 1

However, when running on real, near-term QPUs we care about what
particular physical qubits our program will run on. In fact, we may want
to run the same program on an assortment of different qubits. This is
where using ``QubitPlaceholder``\s comes in.

.. testsetup:: placeholders

   from pyquil import Program
   from pyquil.gates import H, CNOT

.. testcode:: placeholders

    from pyquil.quilatom import QubitPlaceholder
    q0 = QubitPlaceholder()
    q1 = QubitPlaceholder()
    p = Program(H(q0), CNOT(q0, q1))
    print(p)

.. testoutput:: placeholders
   :hide:

    H Placeholder(QubitPlaceholder(0x...))
    CNOT Placeholder(QubitPlaceholder(0x...)) Placeholder(QubitPlaceholder(0x...)) 

.. parsed-literal::

    H Placeholder(QubitPlaceholder(0x600002DEB5B0))
    CNOT Placeholder(QubitPlaceholder(0x600002DEB5B0)) Placeholder(QubitPlaceholder(0x600002DEABB0))

Addressing qubits
=================

If your program uses ``QubitPlaceholder``\s, the placeholders must be resolved before your program can
be run. If you try to run a program with unresolved placeholders, you will get an error:

.. code:: python

    print(p.out())

.. parsed-literal::

    RuntimeError: Qubit q4402789176 has not been assigned an index

Instead, you must explicitly map the placeholders to physical qubits. By
default, the function :py:func:`~pyquil.quil.address_qubits` will address qubits from 0 to
N, skipping indices that are already used in the program.

.. testcode:: placeholders

    from pyquil.quil import address_qubits
    print(address_qubits(p))

.. testoutput:: placeholders

    H 0
    CNOT 0 1

The real power comes into play when you provide an explicit mapping:

.. testcode:: placeholders

    print(address_qubits(p, qubit_mapping={
        q0: 14,
        q1: 19,
    }))

.. testoutput:: placeholders

    H 14
    CNOT 14 19

As an alternative to a mapping, you can consider using :py:meth:`~pyquil.quil.Program.resolve_placeholders_with_custom_resolvers`.
This method accepts any function that takes a placeholder as an argument, and returns a fixed value for that placeholder (or
``None``, if you want it to remain unresolved).

.. testsetup:: placeholders

    from typing import Optional
    from pyquil import Program, get_qc
    from pyquil.gates import H, CNOT
    from pyquil.quilatom import QubitPlaceholder

.. testcode:: placeholders

    q0 = QubitPlaceholder()
    q1 = QubitPlaceholder()
    p = Program(H(q0), CNOT(q0, q1))
    qc = get_qc("2q-qvm")

    def qubit_resolver(placeholder: QubitPlaceholder) -> Optional[int]:
        if placeholder == q0:
            return 0
        if placeholder == q1:
            return None

    p.resolve_placeholders_with_custom_resolvers(qubit_resolver=qubit_resolver)
    print(p)

.. testoutput:: placeholders

   H 0
   CNOT 0 Placeholder(...)

Requesting a register of qubit placeholders
===========================================

Usually, your algorithm will use an assortment of qubits. You can use
the convenience function :py:meth:`~pyquil.quilatom.QubitPlaceholder.register` to request a
register of qubits to build your program.

.. testsetup:: register

    from pyquil import Program
    from pyquil.gates import H
    from pyquil.quilatom import QubitPlaceholder
    from pyquil.quil import address_qubits

.. testcode:: register

    qbyte = QubitPlaceholder.register(8)
    p_evens = Program(H(q) for q in qbyte)
    print(address_qubits(p_evens, {q: i*2 for i, q in enumerate(qbyte)}))


.. testoutput:: register

    H 0
    H 2
    H 4
    H 6
    H 8
    H 10
    H 12
    H 14

**********************
Classical control flow
**********************

Here are a couple quick examples that show how much richer a Quil program
can be with classical control flow.

.. warning::
    Dynamic control flow can have unexpected effects on readout data. See :ref:`accessing_raw_execution_data` for more information.

While loops
===========

In this first example, we create a while loop by following these steps:

1. Declare a register called ``flag_register`` to use as a boolean test for looping.

2. Initialize this register to ``1``, so our while loop will execute. This is often called the
   *loop preamble* or *loop initialization*.

3. Write the body of the loop in its own :py:class:`~pyquil.quil.Program`. This will be a
   program that applies an :math:`X` gate followed by an :math:`H` gate on our
   qubit.

4. Use the :py:func:`~pyquil.quil.Program.while_do` method to add control flow.

5. Call :py:meth:`~pyquil.quil.Program.resolve_label_placeholders` to resolve the label placeholders inserted by ``while_do``.

.. testcode:: control-flow

    from pyquil import Program
    from pyquil.gates import *

    # Initialize the Program and declare a 1 bit memory space for our boolean flag
    outer_loop = Program()
    flag_register = outer_loop.declare('flag_register', 'BIT')

    # Set the initial flag value to 1
    outer_loop += MOVE(flag_register, 1)

    # Define the body of the loop with a new Program
    inner_loop = Program()
    inner_loop += Program(X(0), H(0))
    inner_loop += MEASURE(0, flag_register)

    # Run inner_loop in a loop until flag_register is 0
    outer_loop.while_do(flag_register, inner_loop)
    outer_loop.resolve_label_placeholders()

    print(outer_loop)

.. testoutput:: control-flow

    DECLARE flag_register BIT[1]
    MOVE flag_register[0] 1
    LABEL @START_0
    JUMP-UNLESS @END_0 flag_register[0]
    X 0
    H 0
    MEASURE 0 flag_register[0]
    JUMP @START_0
    LABEL @END_0

Notice that the ``outer_loop`` program applied a Quil instruction directly to a
classical register.  There are several classical commands that can be used in this fashion:

- ``NOT`` which flips a classical bit
- ``AND`` which operates on two classical bits
- ``IOR`` which operates on two classical bits
- ``MOVE`` which moves the value of a classical bit at one classical address into another
- ``EXCHANGE`` which swaps the value of two classical bits

If, then
========

In this next example, we show how to do conditional branching in the
form of the traditional ``if`` construct as in many programming
languages. Much like the last example, we construct programs for each
branch of the ``if``, and put it all together by using the :py:func:`~pyquil.quil.Program.if_then`
method.

.. testcode:: control-flow

    # Declare our memory spaces
    branching_prog = Program()
    test_register = branching_prog.declare('test_register', 'BIT')
    ro = branching_prog.declare('ro', 'BIT')

    # Construct each branch of our if-statement. We can have empty branches
    # simply by having empty programs.
    then_branch = Program(X(0))
    else_branch = Program()

    # Construct our program so that the result in test_register is equally likely to be a 0 or 1
    branching_prog += H(1)
    branching_prog += MEASURE(1, test_register)

    # Add the conditional branching
    branching_prog.if_then(test_register, then_branch, else_branch)

    # Measure qubit 0 into our readout register
    branching_prog += MEASURE(0, ro)
    branching_prog.resolve_label_placeholders()

    print(branching_prog)

.. testoutput:: control-flow

    DECLARE ro BIT[1]
    DECLARE test_register BIT[1]
    H 1
    MEASURE 1 test_register[0]
    JUMP-WHEN @THEN_0 test_register[0]
    JUMP @END_0
    LABEL @THEN_0
    X 0
    LABEL @END_0
    MEASURE 0 ro[0]

We can run this program a few times to see what we get in the readout register ``ro``.

.. testcode:: control-flow

    from pyquil import get_qc

    qc = get_qc("2q-qvm")
    branching_prog.wrap_in_numshots_loop(10)
    result = qc.run(branching_prog)
    print(result.readout_data['test_register'])

.. testoutput:: control-flow
    :hide:

    [[...]
     [...]
     [...]
     [...]
     [...]
     [...]
     [...]
     [...]
     [...]
     [...]]

.. parsed-literal::

    [[1]
     [1]
     [1]
     [0]
     [1]
     [0]
     [0]
     [1]
     [1]
     [0]]


**********************
Pauli Operator Algebra
**********************

Many algorithms require manipulating sums of Pauli combinations, such as
:math:`\sigma = \frac{1}{2}I - \frac{3}{4}X_0Y_1Z_3 + (5-2i)Z_1X_2,` where
:math:`G_n` indicates the gate :math:`G` acting on qubit :math:`n`. We
can represent such sums by constructing ``PauliTerm`` and ``PauliSum``.
The above sum can be constructed as follows:

.. testcode:: pauli-algebra

    from pyquil.paulis import ID, sX, sY, sZ

    # Pauli term takes an operator "X", "Y", "Z", or "I"; a qubit to act on, and
    # an optional coefficient.
    a = 0.5 * ID()
    b = -0.75 * sX(0) * sY(1) * sZ(3)
    c = (5-2j) * sZ(1) * sX(2)

    # Construct a sum of Pauli terms.
    sigma = a + b + c
    print(f"sigma = {sigma}")

.. testoutput:: pauli-algebra

    sigma = (0.5+0j)*I + (-0.75+0j)*X0*Y1*Z3 + (5-2j)*Z1*X2

Right now, the primary thing one can do with Pauli terms and sums is to construct the
exponential of the Pauli term, i.e., :math:`\exp[-i\beta\sigma]`.  This is
accomplished by constructing a parameterized Quil program that is evaluated
when passed values for the coefficients of the angle :math:`\beta`.

Related to exponentiating Pauli sums, we provide utility functions for finding
the commuting subgroups of a Pauli sum and approximating the exponential with the
Suzuki-Trotter approximation through fourth order.

When arithmetic is done with Pauli sums, simplification is automatically
done.

The following shows an instructive example of all three.

.. testcode:: pauli-algebra

    from pyquil.paulis import exponential_map

    sigma_cubed = sigma * sigma * sigma
    print(f"Simplified: {sigma_cubed}\n")

    # Produce Quil code to compute exp[iX]
    H = -1.0 * sX(0)
    print(f"Quil to compute exp[iX] on qubit 0:\n"
           f"{exponential_map(H)(1.0)}")

.. testoutput:: pauli-algebra

    Simplified: (32.46875-30j)*I + (-16.734375+15j)*X0*Y1*Z3 + (71.5625-144.625j)*Z1*X2

    Quil to compute exp[iX] on qubit 0:
    H 0
    RZ(-2) 0
    H 0

``exponential_map`` returns a function allowing you to fill in a multiplicative
constant later. This commonly occurs in variational algorithms. The function
``exponential_map`` is used to compute :math:`\exp[-i \alpha H]` without explicitly filling in a
value for :math:`\alpha`.

.. testcode:: pauli-algebra

    expH = exponential_map(H)
    print(f"0:\n{expH(0.0)}\n")
    print(f"1:\n{expH(1.0)}\n")
    print(f"2:\n{expH(2.0)}")

.. testoutput:: pauli-algebra

    0:
    H 0
    RZ(0) 0
    H 0

    1:
    H 0
    RZ(-2) 0
    H 0

    2:
    H 0
    RZ(-4) 0
    H 0

To take it one step further, you can use :ref:`parametric_compilation` with ``exponential_map``. For instance:

.. testsetup:: pauli-algebra

   from pyquil import Program

.. testcode:: pauli-algebra

    ham = sZ(0) * sZ(1)
    prog = Program()
    theta = prog.declare('theta', 'REAL')
    prog += exponential_map(ham)(theta)


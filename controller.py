"""The baseline: stand up, and keep standing.

Ankle pitch from the projected gravity vector, its rate, and its integral — a PID on the lean of
the trunk, mirrored on the right leg because the right leg's axes are mirrored. Nothing else: the
duck does not move toward the cone, and scores the `stood` point on every seed. The player's first
edit is what beats it.

Standard library only: this is a `python` submission and runs inside CPython-WASI.
"""
DT = 0.02
L_ANKLE, R_ANKLE = 4, 13
KP, KD, KI = 0.8, 0.05, 1.0

integral = 0.0


def step(obs):
    global integral
    gx, pitch_rate = obs[3], obs[1]
    integral = max(-0.5, min(0.5, integral + gx * DT))
    ankle = KP * gx + KD * pitch_rate + KI * integral
    act = [0.0] * 14
    act[L_ANKLE], act[R_ANKLE] = ankle, -ankle
    return act

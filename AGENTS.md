# Duck Jam — round-01-runway 1.0.0 — The Runway

You are helping a player write a controller for a simulated microduck robot. The controller is
`controller.py`, pure Python 3.12, **standard library only** (no numpy, no torch: the sandbox has
none). It runs at 50 Hz inside a WebAssembly sandbox on the player's machine and in the Arena.

## The function

```python
def step(obs: list[float]) -> list[float]:   # 63 in, 14 out
```

`obs` has 61 + 2 floats. `act` is 14 joint deltas in radians, added to the STAND pose and clipped
by the runner. Module-level code runs once per seed; globals persist within a seed and reset between
seeds. `print()` goes to the player's log. `random` is seeded per seed. Do not read the clock.

## obs[0:61] — the robot, identical in every round

| slice | name | unit |
|---|---|---|
| 0–2 | base_ang_vel | rad/s, body frame |
| 3–5 | projected_gravity | unit vector, body frame; [0, 0, -1] when upright |
| 6–19 | joint_pos | rad, relative to STAND, actuator order below |
| 20–33 | joint_vel | rad/s |
| 34–47 | last_action | rad, the previous act |
| 48–60 | command | vx, vy, vtheta, neck_pitch, head_pitch, head_yaw, head_roll, body_x, body_y, body_z, body_roll, body_pitch, body_yaw — written by the round |

Actuator order: left_hip_yaw, left_hip_roll, left_hip_pitch, left_knee, left_ankle, neck_pitch, head_pitch, head_yaw, head_roll, right_hip_yaw, right_hip_roll, right_hip_pitch, right_knee, right_ankle. Legs are indices 0–4 and 9–13.

## obs[61:63] — this round's task_obs

| index | name | unit | range |
|---|---|---|---|
| 61 | goal_dx | m | −6 … 6 |
| 62 | goal_dy | m | −6 … 6 |

Body frame: relative to the base, in its yaw frame.

## This round

## Round 01 — The Runway

> **GET TO THE CONE.** A cone stands two to four metres away, somewhere in front of you. Reach it
> before the clock does. Fall and the seed is over.

The first round of Duck Jam Season 1, specified in
[DJ5 — Challenge design & scoring](../../docs/specs/dj5-challenge-design-and-scoring.md) §Round 01
and shaped as [DJ2](../../docs/specs/dj2-contract-and-challenge-spec.md) writes a challenge.

### What changes between seeds

| parameter | distribution |
|---|---|
| `distance` | uniform 2.0 – 4.0 m |
| `bearing` | uniform −1.0 – 1.0 rad from the start heading |

Nothing else. The duck starts from the STAND keyframe at the origin with the runner's own small
tilt and joint offset, and the cone never moves.

### What the duck sees

`task_obs` is two floats — `goal_dx`, `goal_dy`: the cone in the duck's own yaw frame, metres. A
controller that steers on `atan2(goal_dy, goal_dx)` and stops on `hypot(goal_dx, goal_dy) < 0.15`
needs nothing else.

The command block asks a walking policy for 0.4 m/s toward the cone, turning at
`clip(1.5 · atan2(dy, dx), ±0.6)` rad/s, and all thirteen zeros once inside the reach radius — so
a policy that obeys its command stops on the cone. A `python` or `wasm` controller is free to
ignore it and decide its own gait and heading.

### How a seed ends

| reason | condition | failure |
|---|---|---|
| `fell` | base under 0.06 m | yes — the seed scores 0 |
| `out_of_bounds` | base further than 6 m from the origin | yes — the seed scores 0 |
| `reached` | base within 0.15 m of the cone | no — success, and the seed ends early |
| timeout | 1 250 steps, 25 s | no |

### Score, 0 – 10

| term | value | range |
|---|---|---|
| stood | 1 if the seed did not fail | 0 – 1 |
| progress | 6 × the fraction of the start distance closed by the **closest** approach | 0 – 6 |
| arrival | 3 × (1 − seconds / 25) if the cone was reached | 0 – 3 |

Closest approach, not final position, so a duck that reaches the cone and walks on is scored for
having reached it. The aggregate over the seed list is the mean.

### The ladder

Four rungs over the thirty-two evaluation seeds, `0-31`, measured by
[`prototypes/cd1-actuator-ladder/ladder.py`](../../prototypes/cd1-actuator-ladder/ladder.py) on
this machine (Apple Silicon, one core); `results/ladder.json` beside it holds every seed's score,
metrics and trace hash.

The Arena scores on the **BAM M6 XL330 servos** (`bam-m6-xl330@62bd8ce12154`) — the actuator
`arena/actuator.py` builds and every `microduck_rl` policy is trained against. That is the
left-hand column, and it is the round's. The right-hand column is the scene's idealised XML
position actuators (`xml-position`), which no published policy has ever seen; it is here because
the two are not the same round, and because the difference is the whole of ticket **t-0ux8rum**.
Until that ticket was fixed, `arena/runner.py` drove the right-hand column and the Arena scored
every policy on an actuator none of them was trained against.

| rung | kind | **BAM servos** | worst | reached | `xml-position` | worst | reached |
|---|---|---|---|---|---|---|---|
| zero — fourteen zeros | `zero` | **0.000** | 0.000 | 0 / 32 | 0.000 | 0.000 | 0 / 32 |
| baseline — the stander, `baseline/controller.py` | `python` | **1.007** | 1.000 | 0 / 32 | 0.000 | 0.000 | 0 / 32 |
| steps — a hand-written stepping gait, [DJ5's study](../../prototypes/dj5-round01/controllers/steps.py) | `python` | **1.005** | 1.000 | 0 / 32 | 1.005 | 1.000 | 0 / 32 |
| the walker — `alpha_walking.onnx`, entered as it is | `onnx` | **7.808** | 6.747 | 31 / 32 | 8.019 | 7.310 | 32 / 32 |

The BAM column is DJ5 §The ladder's measured table, every rung inside 0.05 of it — 1.007 against
1.008, 1.005 against 1.005, 7.808 against 7.843. It is measured here through the package runner
and this package rather than through the study's prototype, so the two now agree by construction.
It differs from the study in one seed: on seed 2 the walker closes to 0.168 m, just outside the
0.15 m circle, and times out instead of reaching. Zero falls at 1.08 – 1.66 s, the walker reaches
in 12.1 – 23.3 s.

The right-hand column is what the Arena scored before **t-0ux8rum** was fixed, and it is why
ticket **t-08g5f3a** — the prototype and the runner disagreeing on this round's baseline — was
filed. The baseline's ankle PID is tuned for a servo that lags its command; against joints that
follow it exactly, the duck sinks under the 0.06 m floor at 2.30 – 2.48 s on all thirty-two seeds
and scores nothing. The stiffer stepping gait — ankle gain 4 against the baseline's 0.8 — survives
either actuator, and the walker scores *higher* on idealised joints because they deliver the
0.4 m/s the round asks for and the servos only approximate. **No number in the right-hand column
is the round's.**

The servos cost more, and this ladder is where to read how much: about 48 core-seconds on BAM
against about 16 on the position actuators over three runs of the table. That ×3 is more than the
actuator's own ×2.5 (DJ1 §Throughput), and the difference is the baseline rung — on the idealised
actuators it falls at 2.3 s and the seed ends there, while on the servos it stands all 25 s of
every seed. A seed that runs to the end costs the actuator's ratio; a seed that ends early costs
what it ran. `results/ladder.json` carries each rung's core-seconds for the run it was cut from.

Nothing in this round's own code depends on which column is true: `tests/test_challenge.py` pins
the annulus, the three ways a seed ends and the three score terms without simulating, and
`duckjam check` passes its seven checks against the actuator it is run on.

### Playing it

```
duckjam play --seeds 5          # the first five local seeds, 1000-1004
duckjam play --seeds eval       # the thirty-two the live board scores
duckjam check                   # the conformance suite, against the round's [proof]
```

`baseline/` is what the Forge template hands a player: `controller.py` is fourteen lines of
standard-library Python that stands and never leaves the origin. `[proof]` in `challenge.toml` is
the published walker instead, because a proof that never approaches the cone proves nothing about
the round being beatable.

Episode 25 s; score in 0.0 … 10.0, higher is better; a seed ending in `fell` or `out_of_bounds` scores 0.0. Evaluation seeds 0-31, public; local play draws from 1000-1999.

## Commands

    uv run duckjam play              # five local seeds, one line each, then the aggregate
    uv run duckjam play --seeds eval # the leaderboard's seeds
    uv run duckjam watch             # replay the worst seed of the last play
    uv run duckjam submit            # smoke test, then enter the jam with HEAD (must be pushed)

## Rules

- Change `controller.py` and files beside it. Do not change `duckjam.toml`, `pyproject.toml` or
  `uv.lock`; do not add dependencies — none can be installed in the sandbox.
- A run that is refused (the log says why: a budget, an import, a non-finite action) fails the
  whole submission. Run `duckjam play` before every `submit`.
- Every seed must be deterministic: the same code on the same seed gives the same trace.

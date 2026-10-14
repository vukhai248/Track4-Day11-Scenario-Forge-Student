"""Part A: read a rollout. TODO 1, 2 and 9 live here; the helpers below them are given."""
from __future__ import annotations

import numpy as np

from avsim import core

G = 9.81
HALF_EGO = core.CAR[0] / 2   # 2.3 m: half the ego's length


def ego_events(R: core.Rollout, k: int) -> list[dict]:
    """Failure events involving the ego in scenario k, earliest first (given).

    event["kind"] is "contact" (the boxes touched) or "block" (the ego's body stopped the pedestrian P1 on the
    crosswalk: pedestrians never walk into a car, so this is how a planner that stops too late fails them)."""
    return [e for e in R.events[k] if e["a"] == "ego" or e["b"] == "ego"]


def min_ttc(R: core.Rollout, cap: float = 10.0) -> np.ndarray:
    """TODO 1. (K,) smallest time-to-collision between the ego and whatever it is following, capped at `cap` s.

    - The ego's leader at frame f is R.EGO[k, f, 3] (an actor index, -1 = nothing ahead).
    - Gap is bumper to bumper along the ego's heading: lon - 2.3 - (leader length / 2), where
      lon = (x_leader - x_ego) * hx_ego + (z_leader - z_ego) * hz_ego (the leader's position seen from the ego) and
      2.3 is half the ego's length. Leader length: core.LEN[j] for actor j; use 0.3 m as the half-length of a
      pedestrian. Clip the gap at 0.
    - TTC = gap / (v_ego - v_leader), only while the ego is closing in by more than 0.1 m/s.
    - A scenario where the ego crashed (see ego_events) returns 0.
    Shapes: R.F is (K, NF, N, 7) with x, z, hx, hz, v, a, d; core.IX["ego"] is the ego's actor index.
    Vectorise over frames (a Python loop over 481 frames x K scenarios is too slow for Part C).
    """
    F = R.F
    K, NF, N, _ = F.shape
    EGO_I = core.IX["ego"]
    ex = F[:, :, EGO_I, 0]
    ez = F[:, :, EGO_I, 1]
    ehx = F[:, :, EGO_I, 2]
    ehz = F[:, :, EGO_I, 3]
    ev = F[:, :, EGO_I, 4]
    L = R.EGO[:, :, 3].astype(int)  # (K, NF)
    has = L >= 0
    Lc = np.clip(L, 0, N - 1)
    # gather leader state via take_along_axis
    Fx0 = F[..., 0]
    Fx1 = F[..., 1]
    Fv = F[..., 4]
    lx = np.take_along_axis(Fx0, Lc[..., None], axis=2)[..., 0]
    lz = np.take_along_axis(Fx1, Lc[..., None], axis=2)[..., 0]
    lv = np.take_along_axis(Fv, Lc[..., None], axis=2)[..., 0]
    # leader half length: 0.3 for peds, else LEN/2
    if R.actors is not None and len(R.actors) == N:
        is_ped = np.array([a.kind == "ped" for a in R.actors])
        lens = np.array([a.dims[0] for a in R.actors], dtype=float)
    else:
        base_n = len(core.LEN)
        if N == base_n:
            is_ped = np.array(list(core.PEDS))
            lens = np.array(core.LEN, dtype=float)
        else:
            # pad: extra hazard actors; guess ped by id prefix? fall back: H* ped/bike treated via dims
            is_ped = np.zeros(N, dtype=bool)
            is_ped[:base_n] = np.array(list(core.PEDS))
            lens = np.zeros(N)
            lens[:base_n] = np.array(core.LEN, dtype=float)
            for j in range(base_n, N):
                a = R.actors[j] if R.actors is not None else None
                if a is not None:
                    is_ped[j] = (a.kind == "ped")
                    lens[j] = float(a.dims[0])
                else:
                    lens[j] = 4.6
    half = np.where(is_ped, 0.3, lens / 2.0)  # (N,)
    hlead = half[Lc]
    lon = (lx - ex) * ehx + (lz - ez) * ehz
    gap = np.maximum(lon - 2.3 - hlead, 0.0)
    dv = ev - lv
    ok = has & (dv > 0.1)
    ttc = np.where(ok, gap / np.maximum(dv, 1e-6), np.inf)
    out = np.minimum(cap, ttc.min(axis=1))
    # crashed scenarios -> 0
    for k in range(K):
        if ego_events(R, k):
            out[k] = 0.0
    return out


def contact_type(R: core.Rollout, k: int, event: dict) -> str:
    """TODO 2. 'front' (the ego ran into it), 'rear' (it ran into the ego) or 'side', at the contact frame.

    Put the other actor in the ego's frame: lon = r . h, lat = -r_x h_z + r_z h_x with h = (hx, hz) of the ego.
    'front' if lon > 2.3 and |lat| < 1.6; 'rear' if lon < -2.3 and |lat| < 1.6; otherwise 'side'.
    """
    f = int(event["f"])
    ids = R.ids
    a, b = event["a"], event["b"]
    other_id = b if a == "ego" else a
    ego_idx = ids.index("ego")
    other_idx = ids.index(other_id)
    ego_state = R.F[k, f, ego_idx]
    oth_state = R.F[k, f, other_idx]
    rx = float(oth_state[0] - ego_state[0])
    rz = float(oth_state[1] - ego_state[1])
    hx, hz = float(ego_state[2]), float(ego_state[3])
    lon = rx * hx + rz * hz
    lat = -rx * hz + rz * hx
    if lon > 2.3 and abs(lat) < 1.6:
        return "front"
    if lon < -2.3 and abs(lat) < 1.6:
        return "rear"
    return "side"


def progress_metrics(R: core.Rollout) -> tuple[np.ndarray, np.ndarray]:
    """TODO 9. Two (K,) arrays: the distance the ego covers in the 24 s (sum of frame-to-frame steps, metres),
    and the number of frames where the ego brakes harder than 3 m/s^2 (acceleration column < -3)."""
    EGO_I = core.IX["ego"]
    x = R.F[:, :, EGO_I, 0]
    z = R.F[:, :, EGO_I, 1]
    a = R.F[:, :, EGO_I, 5]
    dist = np.sum(np.hypot(np.diff(x, axis=1), np.diff(z, axis=1)), axis=1)
    harsh = np.sum(a < -3.0, axis=1).astype(int)
    return dist, harsh


# ---------------------------------------------------------------- given helpers

def pair_min_ttc(R, follower, leader, cap=10.0, lat_max=2.2, leader_vmin=-1.0):
    """(K,) smallest TTC of `follower` running into `leader` while they share a corridor."""
    F = R.F
    a, b = F[:, :, core.IX[follower]], F[:, :, core.IX[leader]]
    rx, rz = b[..., 0] - a[..., 0], b[..., 1] - a[..., 1]
    lon = rx * a[..., 2] + rz * a[..., 3]
    lat = -rx * a[..., 3] + rz * a[..., 2]
    gap = np.maximum(lon - core.LEN[core.IX[follower]] / 2 - core.LEN[core.IX[leader]] / 2, 0.0)
    dv = a[..., 4] - b[..., 4]
    ok = (lon > 0) & (np.abs(lat) < lat_max) & (dv > 0.1) & (b[..., 4] >= leader_vmin)
    ttc = np.where(ok, gap / np.maximum(dv, 1e-6), np.inf)
    return np.minimum(cap, ttc.min(1))


def ped_room(R, cap=30.0):
    """(K,) smallest stopping room [m] left while the crossing pedestrian is in the ego's lane
    (distance to them minus the ego's braking distance at mu*g). Negative = could not have stopped."""
    e, p = R.F[:, :, core.IX["ego"]], R.F[:, :, core.IX["P1"]]
    mu = np.asarray(R.params["mu"])[:, None]
    inlane = np.abs(p[..., 1] - e[..., 1]) < 1.9
    ahead = p[..., 0] - e[..., 0] - HALF_EGO
    room = np.where(inlane & (ahead > -1.0), ahead - e[..., 4] ** 2 / (2 * mu * G), cap)
    return np.clip(room.min(1), -cap, cap)

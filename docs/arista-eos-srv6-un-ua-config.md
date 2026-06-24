# Arista EOS SRv6 uN + uA Config — Plane 1

Complete **Arista EOS** configuration template for **MRC Plane 1**, covering both **uN** (node) and **uA** (adjacency) micro-segments on a **T0 leaf** and **T1 spine**. Syntax is validated against the Arista **SRv6 uN Support TOI** (EOS 4.34.2F) and **SRv6 uA Support TOI** (EOS 4.35.2 GA).

For the conceptual walkthrough of how packets traverse this plane, see [SRv6 Plane 1 — Packet Traversal](srv6-plane1-packet-traversal.md). For a SONiC vs Arista comparison and rack-wide addressing templates, see [SRv6 uN uSID — Leaf/Spine Config (SONiC vs Arista)](srv6-usid-leaf-spine-config.md).

!!! note "Scope"
    This is a **lab-ready Plane 1 slice** — one leaf (`leaf1-p1`) and one spine (`spine1-p1`) with illustrative GPU downlinks. Extend Ethernet port patterns and static routes for additional leaves in the plane. Replace management addresses and link-local next hops for production.

---

## Addressing plan

| Resource | Prefix / uSID | Range | Notes |
|----------|---------------|-------|-------|
| uSID block | `fc00:1::/32` | — | Domain `PLANE1-DOMAIN`, F3216 format |
| leaf1-p1 uN | `fc00:1:1::/48` | GIB `0x0001` | Node SID — shift-and-lookup transit |
| leaf2-p1 uN | `fc00:1:2::/48` | GIB `0x0002` | Referenced in static routes / verification |
| spine1-p1 uN | `fc00:1:6501::/48` | GIB `0x6501` | Spine tier node SID |
| leaf1 → spine uA | `fc00:1:e001::/48` | LIB `0xe001` | On leaf1 `Ethernet64` uplink |
| spine → leaf1 uA | `fc00:1:e101::/48` | LIB `0xe101` | On spine `Ethernet1` downlink |
| spine → leaf2 uA | `fc00:1:e102::/48` | LIB `0xe102` | On spine `Ethernet2` downlink |
| leaf2 → server uA | `fc00:1:f001::/48` | LIB `0xf001` | Server-facing adjacency (leaf2) |

**uSID allocation discipline:**

- **GIB** (`0x0001`–`0xDFFF`) — node segments (uN)
- **LIB** (`0xE000`–`0xFFFF`) — adjacency segments (uA)

---

## What the config covers

| Section | Device | Contents |
|---------|--------|----------|
| **Part A** | `leaf1-p1` | Loopback uN, GPU downlinks, uplink uA on `Ethernet64`, `router srv6` domain/locator, static route to spine uN, ECN on transit ports, MGMT VRF |
| **Part B** | `spine1-p1` | Loopback uN, per-leaf downlinks with uA, `router srv6` locator, static routes to leaf uNs, ECN on all downlinks, MGMT VRF |
| **Verification** | Both | `show srv6` commands, `ping srv6` / `traceroute srv6` examples, uA neighbor-discovery checks |
| **Architecture notes** | — | When to use uN vs uA, mixing segments in one uSID container, ECMP caveat |

---

## uN vs uA — quick reference

| Behavior | CLI | Forwarding |
|----------|-----|------------|
| **uN** | `locator … end usid <value>` | Match local locator → shift 16b → static FIB lookup |
| **uA** | `adjacency-segment srv6 … behavior end.x p2p link-local` | Match adjacency uSID → forward out **that interface**, bypass FIB |

Both coexist in the same SFIB. Standard MRC spraying uses uN throughout; uA is for explicit link steering (traffic engineering, failure avoidance).

---

## Full configuration

Source file: [Arista_EOS_SRv6_uN_uA_Config.txt](Arista_EOS_SRv6_uN_uA_Config.txt)

```eos
--8<-- "Arista_EOS_SRv6_uN_uA_Config.txt"
```

!!! tip "Applying in the lab"
    1. Enable `ipv6 unicast-routing` before SRv6 stanzas.
    2. Allow **150–200 seconds** after link-up for uA link-local discovery (`show ipv6 nd ra neighbors`).
    3. Confirm locators are **active** with `show srv6 locator` and adjacency segments with `show srv6 adjacency-segments`.
    4. Test uN reachability: `ping srv6 sid fc00:1:6501:: via segment-list fc00:1:1::`

---

## Related pages

- [SRv6 Plane 1 — Packet Traversal](srv6-plane1-packet-traversal.md)
- [SRv6 uN uSID — Leaf/Spine Config (SONiC vs Arista)](srv6-usid-leaf-spine-config.md)
- [MRC Packet Structure — SRv6 + Entropy Value](generated/srv6-mrc-packet-ev-header.md)
- [Glossary](glossary.md)

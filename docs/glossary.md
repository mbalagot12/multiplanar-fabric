# Glossary

Definitions for terms used throughout this MRC networking primer. Terms are grouped by topic; use your browser search (⌘F / Ctrl+F) to jump to a specific entry.

!!! tip "Quick links"
    [MRC & transport](#mrc-transport) · [SRv6 & segment routing](#srv6-segment-routing) · [uSID micro-behaviors](#usid-micro-behaviors) · [Behavior flavors (PSP, USD, …)](#behavior-flavors) · [Addressing & packets](#addressing-packets) · [SONiC stack](#sonic-stack) · [Hardware & platforms](#hardware-platforms) · [Protocols & networking](#protocols-networking)

---

## MRC & transport

### MRC (Multipath Reliable Connection)

OCP-standard RDMA transport for AI training clusters. Extends RoCEv2 with multipath packet spraying, transport-layer path health management, selective retransmission, and packet trimming. Defined in [OCP MRC Rev 1.0](https://www.opencompute.org/documents/ocp-mrc-1-0-pdf).

### MRC engine

Logic in a SmartNIC that generates EVs, selects paths per packet, handles SACK/NACK feedback, retransmits lost data, and retires failed paths — without application changes.

### EV (Entropy Value)

A **32-bit per-packet identifier** striped across the outer IPv6 **flow label** (20 bits) and **UDP source port** (16 bits). Generated at QP startup (typically 128–256 values per QP, split across planes). Used for **path health feedback** in SACK/NACK; **not used by switches for forwarding** in MRC.

### Plane

One of **eight independent** leaf–spine fabric networks. NIC *n* on every node connects only to the leaf of plane *n*. Traffic on plane 1 never crosses into plane 2.

### Multipath / packet spray

Sending successive packets from the same QP over different paths (different EVs → different SRv6 uSID stacks) to spread load and survive failures without ECMP.

### SACK / NACK

Selective acknowledgment and negative acknowledgment messages from the receiver NIC. Echo the EV so the sender's MRC engine knows which path (EV) is healthy, congested, or failed.

### Packet trim / trimming

Congestion signal: switch strips payload but forwards headers. Triggers selective retransmit of missing data — not full QP recovery. Distinct from **loss** (packet dropped → EV retired immediately).

### Lossy Ethernet RDMA

MRC runs over best-effort Ethernet with **PFC disabled**. Reliability and congestion response live in the NIC transport layer, not in switch pause frames.

### QP (Queue Pair)

RDMA connection endpoint between two NICs. MRC assigns a set of EVs and SRv6 path templates per QP at setup time.

### RoCEv2

RDMA over Converged Ethernet v2 — UDP/IP encapsulation of RDMA (typically port 4791). MRC builds on RoCEv2 semantics with extended multipath and feedback.

### Static source routing

Paths are encoded in the packet (SRv6 uSID stack) by the sender NIC. Switches follow pre-provisioned static tables — no runtime route computation.

### Path matrix

Spreadsheet or generated table mapping every **post-shift destination prefix** on each switch to an egress port and next-hop. Required to program MRC leaf/spine static FIBs.

---

## SRv6 & segment routing

### SRv6 (Segment Routing over IPv6)

Source routing where paths are encoded as IPv6 **Segment Identifiers (SIDs)** in the destination address or Segment Routing Header (SRH). Switches execute **local behaviors** bound to each SID.

### Segment / SID (Segment Identifier)

A 128-bit IPv6 address (full SID) or shorter **micro-SID** instructing a node what to do (forward, decapsulate, lookup in VRF, etc.).

### Segment Routing Header (SRH)

IPv6 extension header (next header 43) carrying an ordered list of SIDs. In **uSID** deployments the path is often encoded entirely in the **destination address**, reducing SRH overhead.

### Source routing

Sender specifies the full path; transit nodes do not run dynamic routing protocols to choose next hops. MRC uses static SRv6 source routing on the backend fabric.

### Locator

An IPv6 prefix (typically `/48` in F3216 uSID) identifying a node or domain in the SRv6 addressing hierarchy. All local SIDs for that node are allocated under the locator. Comprises **block + node** portions in uSID format.

### Locator block (uSID block)

The high-order **32-bit** prefix shared across a fabric domain (e.g. `fcbb:bbbb::/32`). Defines the SRv6 address space for the rack or pod.

### Shift-and-lookup

Core **uN** dataplane operation: match local uSID → left-shift the uSID field 16 bits → perform FIB/LPM lookup on the new destination address → forward.

### NEXT-CSID

Compressed-SID instruction executed by **uN** and **uA**: advance to the next 16-bit micro-SID in the carrier by shifting the destination address left.

### CSID (Compressed SID)

A uSID instruction packed into 16 bits within the 128-bit destination address, as opposed to a full 128-bit classic SRv6 SID.

### End behavior

Classic SRv6 local action on a full SID — typically "I am this node; pop/shift and continue or decapsulate." **uN** is the uSID variant of End with NEXT-CSID.

### End.X behavior

Classic SRv6 "cross-connect to a specific adjacency (interface/next-hop)." **uA** is the uSID variant of End.X with NEXT-CSID.

### End.DT46 / uDT46

Decapsulate outer IPv6 and lookup inner packet in a VRF routing table supporting **both** IPv4 and IPv6. Used at PE/NIC decapsulation points in overlay designs.

---

## uSID micro-behaviors

Micro-segment (**uSID**) behaviors are compact 16-bit instructions. In MRC transit fabrics, **uN** dominates; overlay/service behaviors appear at NIC or PE edges.

| Term | Full name | Role in MRC |
|------|-----------|-------------|
| **uN** | uNode / End + NEXT-CSID | **Transit switch**: shift uSID stack, lookup, forward. Every leaf and spine gets a `/48` uN locator. |
| **uA** | uAdjacency / End.X + NEXT-CSID | **Explicit link**: forward out a named interface (and optional next-hop). Used when path matrix pins a specific uplink/downlink. |
| **uDT4** | uDecap + IPv4 table | Decapsulate; lookup inner IPv4 in VRF. |
| **uDT6** | uDecap + IPv6 table | Decapsulate; lookup inner IPv6 in VRF. |
| **uDT46** | uDecap + IPv4/IPv6 table | Decapsulate; lookup inner packet in VRF (dual-stack). NIC decap in overlay demos. |
| **uDX4 / uDX6** | uDecap + cross-connect | Decapsulate and L2/L3 cross-connect to a specific neighbor (uSID variants of End.DX4/DX6). |

### uSID / micro-SID / micro-segment

An extension of SRv6 that packs **multiple 16-bit instructions** into one 128-bit IPv6 destination address (**uSID carrier**), instead of one 128-bit SID per hop.

### uSID carrier

The 128-bit IPv6 destination address layout:

```text
<uSID-Block><Active-uSID><Next-uSID>…<Last-uSID><End-of-Carrier>…
```

Up to six uSIDs fit in F3216 format before padding.

### Active uSID

The leftmost 16-bit uSID slot after the locator block — the instruction the current node executes (compare first 48 bits: block + active uSID).

### End-of-Carrier (EoC)

Reserved uSID value **`0000`**. Marks unused slots; fills remaining bits to complete the 128-bit address after the last real uSID.

### F3216

Standard uSID carrier format: **F** = format name, **32** = block length (bits), **16** = uSID ID length (bits). Required interoperable format per IETF SRv6 uSID compression work and RFC 9800 ecosystem.

### micro-segment domain (Arista EOS)

Shared **uSID block** configuration under `router srv6` → `vrf default`. Defines the F3216 block prefix (`block fcbb:bbbb::/32`) used by all locators in the fabric. See [SRv6-uN-Support.pdf](SRv6-uN-Support.pdf).

### `end usid` (Arista EOS locator)

16-bit uSID value on a **locator** stanza: `prefix micro-segment domain <DOM> end usid 0x0101`. Combined with the domain block, this yields the node’s `/48` uN prefix in System SFIB (e.g. `fcbb:bbbb::/32` + `0x0101` → `fcbb:bbbb:0101::/48`). Same value maps to SONiC `SRV6_MY_LOCATORS` + FRR `static-sids`. See [SRv6 config reference](srv6-usid-leaf-spine-config.md#addressing-plan-f3216--unified-sonic--arista).

### unode

Informal name for **uN** (End with uSIDs) behavior. On Arista EOS, configured via `router srv6` locator + `end usid`, not via 3rd-party OS `micro-segment behavior unode psp-usd` syntax.

### `behavior usid`

FRR/SONiC CLI phrase marking a locator as a **uSID locator** so allocated SIDs use uN/uA/uDT* behaviors instead of classic End/End.X/End.DT*.

---

## Behavior flavors

Flavors modify **how** a behavior handles the SRH/outer header at penultimate or final hop. uN/uA in MRC deployments typically use **PSP + USD**.

### PSP (Penultimate Segment Pop)

On the **penultimate** hop, remove the SRH (or outer encapsulation) before delivery to the final segment. Reduces processing on the endpoint node. With uSID, shift-and-lookup achieves similar efficiency without a full SRH.

### USD (Ultimate Segment Decapsulation)

On the **ultimate** (final) hop, decapsulate the outer IPv6 header cleanly when the node is the destination. Standard flavor paired with PSP for uN/uA.

### PSP/USD

Combined flavor notation; on Arista EOS see `show srv6 capabilities` (PSP, USD, Next-CSID). On SONiC/FRR: `uN (PSP/USD)` in `show segment-routing srv6 sid`.

### Pipe / Uniform (`decap_dscp_mode`)

How a node preserves **DSCP** on decapsulation. **Pipe** copies outer DSCP to inner; **uniform** may remap. Relevant for uDT* service SIDs in ConfigDB (`decap_dscp_mode` field).

---

## Addressing & packets

### Outer / inner IPv6 header

MRC data packets use **IPv6-in-IPv6** encapsulation. The **outer** header carries SRv6 uSID path + EV fields; the **inner** header carries the actual RDMA/RoCE payload path.

### Flow label

20-bit field in the IPv6 header. In MRC, carries the **high 20 bits of the 32-bit EV**.

### UDP source port

In RoCEv2/MRC outer header, carries the **low 16 bits of the EV** (destination port remains 4791 for RoCEv2).

### DA (Destination Address)

IPv6 destination address of the outer header. In MRC, encodes the **uSID carrier** (path); switches match and shift this field.

### FIB (Forwarding Information Base)

Hardware/software forwarding table. After uN shift, lookup hits a **static** FIB entry → egress port.

### LPM (Longest Prefix Match)

Standard IPv6 lookup. uN forwarding uses LPM (or exact static routes) on the **shifted** destination address.

### GUA / ULA

Global Unicast Address / Unique Local Address — common choices for SRv6 locator blocks and underlay links.

---

## SONiC stack

### SONiC (Software for Open Networking in the Cloud)

Open NOS for data center switches. Uses Redis **ConfigDB**, **syncd**/**SAI** for ASIC programming, and **FRR** for routing protocols and SRv6 control plane.

### ConfigDB

SONiC configuration database (Redis DB 4). Source of truth for `SRV6_MY_LOCATORS`, `SRV6_MY_SIDS`, interfaces, etc. Persisted with `config save` to `/etc/sonic/config_db.json`.

### APPDB / APPL_DB

Application database — orchagent writes programmed state (e.g. `SRV6_MY_SID_TABLE`) consumed by syncd/SAI.

### bgpcfgd

SONiC daemon that watches ConfigDB (including SRv6 tables) and compiles changes into **FRR** configuration via the SRv6 Manager module.

### srv6orch

SONiC orchagent module that translates SRv6 MY_SID entries into **SAI** my-SID programming for the ASIC.

### SAI (Switch Abstraction Interface)

Vendor-neutral API between SONiC and switch ASIC SDK. Defines `SAI_MY_SID_ENTRY_*` behaviors including `UN`, `UA`, `DT46`, etc.

### FRR (FRRouting)

Open-source routing suite (zebra, bgpd, staticd, isisd, …) used by SONiC for SRv6 locators, static SIDs, and optional IGP/BGP. CLI shell: **`vtysh`**.

### vtysh

FRR integrated CLI (classic CLI style). On SONiC: `vtysh -c "show segment-routing srv6 locator"`. Ephemeral unless backed by ConfigDB or `frr.conf`.

### zebra

FRR component managing RIB/FIB interaction and SRv6 locator configuration. SRv6 locators are configured under `segment-routing` → `srv6` in zebra/staticd.

### staticd

FRR daemon for static routes and **`static-sids`** SRv6 local SID configuration.

### fpmsyncd

SONiC daemon syncing FRR programming into APPDB for orchagent consumption.

### `static-sids`

FRR configuration subtree for manually assigned local SIDs:

```text
segment-routing → srv6 → static-sids → sid … behavior uN|uA|uDT46 …
```

### `SRV6_MY_LOCATORS` / `SRV6_MY_SIDS`

ConfigDB tables for static SRv6 locator prefixes and local SID-to-behavior mappings. Compiled to FRR by bgpcfgd.

---

## Hardware & platforms

### 7060XE7

Arista data center switch (Broadcom **Tomahawk 6**) used as MRC leaf/spine in this primer's rack diagrams. Supports line-rate SRv6 uN in EOS.

### Tomahawk 5 (TH5)

Broadcom switching ASIC generation in 7060XE7 and related AI fabric switches. SRv6 uSID uN forwarding at line rate in production MRC deployments.

### EOS (Extensible Operating System)

Arista network operating system. SRv6 uN uses **`router srv6`** (micro-segment domain + locator), documented in [SRv6-uN-Support.pdf](SRv6-uN-Support.pdf) (4.34.2F+). Operational: `show srv6 locator`, `show srv6 route`, `ping srv6 sid … via segment-list …`.

### TOI (Transfer of Information)

Arista technical bulletin for new features (e.g. SRv6 uN Support, SRv6 uA Support).

### Spectrum-4 / Spectrum-5

Nvidia Ethernet switch ASICs running SONiC or Cumulus in OpenAI/Microsoft MRC deployments (alongside Arista EOS).

### ConnectX-7 / ConnectX-8 SuperNIC

Nvidia SmartNICs with MRC engine support (400G and 800G per port respectively in this primer).

### Pollara 400

AMD Pensando SmartNIC with OCP MRC Rev 1.0 support on MI350X nodes.

---

## Protocols & networking

### ECMP (Equal-Cost Multi-Path)

Load-sharing across multiple next hops for the same prefix. **Disabled in MRC** — multipath is explicit via EV/SRv6 paths, not hash-based ECMP.

### BGP (Border Gateway Protocol)

Path-vector routing protocol. **Not used** on MRC backend planes (static SRv6 only). May appear in overlay/L3VPN SRv6 service scenarios outside the backend fabric.

### IS-IS

Link-state IGP. Can advertise SRv6 locators and auto-allocate uN/uA in dynamic SRv6 designs. **Disabled in MRC** backend; SR-MPLS IS-IS in EOS manual is a different data plane.

### PFC (Priority Flow Control)

IEEE 802.1Qbb pause-based lossless Ethernet. **Disabled in MRC** — avoids pause storms; NIC handles retry.

### DCQCN

Data Center Quantized Congestion Notification — RoCE congestion control. Not the primary MRC congestion mechanism (trim + SACK-based response instead).

### RDMA

Remote Direct Memory Access — kernel-bypass memory read/write between nodes. MRC adds multipath reliability on top of RoCEv2 RDMA.

### NVLink / NVSwitch

Nvidia intra-node GPU interconnect and switch chip. Handles **local** all-reduce inside a DGX/HGX node — separate from MRC inter-node fabric.

### Infinity Fabric

AMD intra-node interconnect — AMD analogue to NVLink for local GPU traffic.

### OCP (Open Compute Project)

Industry consortium; publishes the **MRC Rev 1.0** specification used throughout this primer.

### Clos / leaf–spine

Two-tier data center topology. Each MRC **plane** is a miniature leaf–spine: nodes → leaf → spine → leaf → nodes (2 fabric hops).

### Leaf / spine

**Leaf**: top-of-rack switch facing compute NICs. **Spine**: aggregation switch connecting leaves within a plane. One pair per plane in the 72-GPU rack reference design.

---

## Abbreviation index (A–Z)

| Abbr. | Expansion |
|-------|-----------|
| **BGP** | Border Gateway Protocol |
| **CSID** | Compressed SID |
| **DA** | Destination Address |
| **DCQCN** | Data Center Quantized Congestion Notification |
| **EoC** | End-of-Carrier |
| **ECMP** | Equal-Cost Multi-Path |
| **EOS** | Extensible Operating System (Arista) |
| **EV** | Entropy Value |
| **FIB** | Forwarding Information Base |
| **FRR** | FRRouting |
| **GUA** | Global Unicast Address |
| **IGP** | Interior Gateway Protocol |
| **LPM** | Longest Prefix Match |
| **MRC** | Multipath Reliable Connection |
| **OCP** | Open Compute Project |
| **PFC** | Priority Flow Control |
| **PSP** | Penultimate Segment Pop |
| **QP** | Queue Pair |
| **RDMA** | Remote Direct Memory Access |
| **RoCEv2** | RDMA over Converged Ethernet v2 |
| **SAI** | Switch Abstraction Interface |
| **SACK** | Selective ACK |
| **SID** | Segment Identifier |
| **SONiC** | Software for Open Networking in the Cloud |
| **SRH** | Segment Routing Header |
| **SRv6** | Segment Routing over IPv6 |
| **TH5** | Tomahawk 5 |
| **TOI** | Transfer of Information (Arista) |
| **uA** | uSID Adjacency (End.X + NEXT-CSID) |
| **uDT46** | uSID Decap + DT46 |
| **uN** | uSID Node (End + NEXT-CSID) |
| **uSID** | micro-SID / micro-segment |
| **USD** | Ultimate Segment Decapsulation |
| **ULA** | Unique Local Address |
| **VRF** | Virtual Routing and Forwarding |

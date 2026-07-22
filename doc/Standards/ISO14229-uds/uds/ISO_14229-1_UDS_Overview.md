# ISO 14229-1 (UDS) — Quick Overview

This is the ISO 14229-1 standard (Unified Diagnostic Services, UDS), which defines the application-layer protocol used for diagnostic communication with electronic control units (ECUs) in vehicles. It specifies the request/response message formats, service IDs, and behavioral rules for diagnostic services like reading/writing data, running routines, controlling communication, and managing security access — independent of the underlying transport (CAN, LIN, Ethernet, etc.).

Below are three key services covered in the standard.

## 1. Diagnostic Service Requirements defined by ISO-14229

### 1.1. General

**Client-server model.** ISO 14229-1 is built around a **client-server** relationship: a diagnostic tester (the **client**) — usually off-board test equipment, though it can be on-board — controls diagnostic functions in an on-vehicle ECU (the **server**, e.g. an engine management system, ABS, or automatic gearbox). The client requests a diagnostic service, and the server performs it and sends response data back. The client role and server role are independent of the underlying data link, and more than one client can exist in the same vehicle system. [ISO 14229-1:2013, Clause 1 Scope; Clause 6.1 General]

**Six service primitives.** For each diagnostic service, the standard defines six service primitives that describe how data moves between the client/server applications and the diagnostics application layer:

1. **Request** — client passes data about a requested service to the diagnostics application layer
2. **Request-confirmation** — confirms to the client that the request data was fully transferred to the server
3. **Indication** — diagnostics application layer passes the request data to the server function
4. **Response** — server passes the requested service's response data (positive or negative) to the diagnostics application layer
5. **Response-confirmation** — confirms to the server that the response data was fully transferred to the client
6. **Confirmation** — diagnostics application layer passes the response data to the client function

Confirmed services use all six primitives (Figure 3); unconfirmed services use only the request / request-confirmation / indication primitives, with no response expected (Figure 4). ISO notes that the service descriptions in the standard itself do not use the two *-confirmation* primitives — data-link-specific implementation documents use them to define service execution reference points (e.g. ECUReset performs the reset once the response has been fully transmitted, signalled by the response-confirm primitive). [ISO 14229-1:2013, Clause 6.1 General]



### 1.1.1 Mapping the communication stack onto the OSI model

**Position in the OSI model.** The standard maps diagnostic communication onto the seven-layer OSI Basic Reference Model (ISO 7498-1 / ISO/IEC 10731): **Unified diagnostic services occupy layer 7 (application layer)**, while the underlying data link (CAN, LIN, FlexRay, Ethernet, etc.) provides **communication services across layers 1–6**. This is what makes UDS transport-independent — the same service definitions apply regardless of which network carries them. The standard's own layer allocation names ISO 14229-2 at the session layer (5), and ISO 15765-2 / ISO 10681-2 / ISO 13400-2 / ISO 17987-2 jointly at *both* the transport (4) and network (3) layers. [ISO 14229-1:2013, Introduction and Table 1]

The ISO document does not go further than that — it does not itself specify where individual AUTOSAR CAN-stack modules (PduR, CanIf, CanDrv, CanTp) sit on the OSI model. 

The mapping below is therefore drawn from general AUTOSAR/ISO 15765 architecture knowledge, not from ISO 14229-1 itself.

![UDS/AUTOSAR communication stack mapped onto the OSI reference model](autosar-uds-osi-mapping.svg)

A few clarifications on that mapping:

- **CanIf → Data Link** and **CanDrv → Physical** are reasonable, commonly used mappings.
- **CanTp → Transport** is correct, but incomplete: ISO 15765-2, which CanTp implements, is titled *"Transport protocol **and network layer** services"* — so CanTp arguably covers Layer 3 as well as Layer 4, rather than Layer 4 alone.
- **PduR → Network layer** is the weakest part of the mapping. PduR is a routing/multiplexing dispatcher between BSW modules (DCM, CanTp, COM), not an OSI Layer-3 entity — it does not perform addressing or routing across physical networks the way a true network-layer protocol does. It is commonly drawn near Layer 3/4 for convenience, but that placement is an approximation rather than an architectural fact.
- Layers 5 and 6 (Session, Presentation) have no dedicated AUTOSAR module; the diagnostic "session" concept (defaultSession, programmingSession, etc.) is itself a Layer-7 UDS concept (DiagnosticSessionControl), not an OSI Layer-5 session.

### 1.2 Services

ISO 14229-1 groups its services into **functional units**, one per clause. The **Diagnostic and Communication Management** functional unit (Clause 9, Table 22 — Clause 10 in the earlier 2011 draft) defines the **10 services** that manage the diagnostic conversation itself: which session is active, whether the server is unlocked, whether the tester is still connected, and how communication and DTC recording behave. The remaining 16 services of the standard sit in the Data Transmission (Clause 10), Stored Data Transmission (Clause 11), InputOutput Control (Clause 12), Routine (Clause 13) and Upload Download (Clause 14) functional units.

| Service                  | What it does                                                                                                                                                                                                                                                                   |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| DiagnosticSessionControl | Enables a diagnostic session in the server. Each session enables a specific set of services and functionality — *which* set is defined by the OEM, not by ISO. Exactly one session is active at a time, and the server starts in defaultSession at power-up.                   |
| ECUReset                 | Forces the server to reset itself, with the resetType parameter selecting the kind of reset (hard, key-off-on, soft, rapid power shutdown). The positive response is sent before the reset executes, and the server comes back in defaultSession.                              |
| SecurityAccess           | Unlocks data and services restricted for security, emissions or safety reasons, via a seed-and-key exchange: the client requests a seed, returns the matching key, and the server unlocks if the key is valid. Only one security level is active at a time.                    |
| CommunicationControl     | Switches transmission and/or reception of certain classes of messages on or off in the server (e.g. normal application communication) — used to quieten the bus for diagnostics.                                                                                               |
| TesterPresent            | Signals that the client is still connected, so previously activated services and communication remain active. This is what holds a server in a non-default session instead of letting it time out back to defaultSession.                                                      |
| AccessTimingParameter    | Reads and changes the default communication timing parameters for as long as the link is active. Offers four modes: read extended set, read currently active, set to given values, set to default. Timings reset to default on any session change.                             |
| SecuredDataTransmission  | Transmits a diagnostic message — or an external-protocol message — in secured mode, protected by cryptographic methods against third-party attack. A security sub-layer above the application layer performs the encryption/decryption; secured links are point-to-point only. |
| ControlDTCSetting        | Stops or resumes the updating of DTC status bits in the server. It only freezes the status bits: it does not switch off fault monitoring, and is not intended to disable failsoft strategies.                                                                                  |
| ResponseOnEvent          | Sets up the server to execute a nominated diagnostic service automatically whenever a specified event occurs, and starts/stops that event logic. Can be set up in any session including defaultSession, and does not require TesterPresent to stay active.                     |
| LinkControl              | Reconfigures the data link — typically to a higher baudrate — to gain bus bandwidth for diagnostics such as programming. The transition is two-stage (verify, then transition) and applies only in a non-default session.                                                      |

[ISO 14229-1:2013, Clause 9.1 Table 22 (service list) and the per-service "Service description" subclauses 9.2.1 – 9.11.1]

### 1.3 Basic UDS Message

### 1.3.1 Message structure: A_SDU, A_PDU and the mandatory parameters

- **A_SDU** (Application layer **Service** Data Unit) — parameters passed across the service primitive, application ↔ application layer; never leaves the ECU. Figure 1: `SA, TA, TAtype, [parameter#1, parameter#2, …]`. [Clause 6.4]
- **A_PDU** (Application layer **Protocol** Data Unit) — "directly constructed from the A_SDU and the layer specific control information A_PCI"; what one application layer sends to its peer. Figure 1: `SA, TA, TAtype, `**`A_PCI`**`, [parameter#1, parameter#2, …]`. [Clause 7.2]

![ISO 14229-1 message structure: A_SDU vs A_PDU](uds-sdu-pdu-format.svg)

**Parameters.** A_SDU per Clause 6.4; A_PDU per Clause 8.2, Tables 9 and 10. A dash means the field does not exist at that level.

| A_SDU       | A_PDU                    | Cvt | What it carries                                                                                     |
| ----------- | ------------------------ | --- | --------------------------------------------------------------------------------------------------- |
| `A_Mtype`   | `MType`                  | M   | Message type: `diagnostics` or `remote diagnostics`. Selects whether the remote address is present. |
| `A_SA`      | `SA`                     | M   | Source address, 2 bytes. Client on a request; responding server on a response.                      |
| `A_TA`      | `TA`                     | M   | Target address, 2 bytes. Server to act on a request; originating client on a response.              |
| `A_TA_type` | `TAtype`                 | M   | `physical` (point-to-point) or `functional` (broadcast). Responses are always physical.             |
| `A_AE`      | `RA`                     | C   | Remote address, 2 bytes. Only when the message type is `remote diagnostics`.                        |
| `A_Length`  | `Length`                 | M   | Byte count of `A_Data`, 4 bytes.                                                                    |
| `A_Data`    | `A_Data`                 | M   | Transmitted bytes. In the A_PDU, starts with the A_PCI — next three rows.                           |
| —           | `A_Data.A_PCI.SI`        | M   | Service identifier, 1 byte.                                                                         |
| —           | `A_Data.Parameter 1`     | S   | Sub-function, for the services that have one.                                                       |
| —           | `A_Data.Parameter 2 … k` | U   | Service-specific data-parameters.                                                                   |
| `A_Result`  | —                        | M   | `ok` / `error`. Request-confirm and response-confirm primitives only; never transmitted.            |

Nesting: `A_PDU` → `A_Data` → `A_PCI` → `SI`. Per-service tables from Clause 9 onwards show `A_Data` only. [Clauses 7.5.5, 8.2.1]

###  1.3.2 A_Data subsection in UDS message

Request = SID + optional sub-function + optional parameter + optional data record:

- **SID** (1 byte) — the service, e.g. `0x22` ReadDataByIdentifier
- **Sub-function** (1 byte, optional) — mode within the service, e.g. `0x01` = start routine for RoutineControl
- **Parameter** (1-3 bytes, optional) — DID, RID, or DTC group/mask
- **Data record** (variable length, optional) — payload written, or option data

Positive response: request SID + `0x40`, echoed parameters, data record. Negative response: fixed 3 bytes — `0x7F`, request SID, 1-byte NRC. [Clause 7.4, Table 3]

![Common UDS message format and field mapping to DCM/DEM services](full-UDS-msg-format.svg)

| Service                    | SID / Response SID | Sub-function                             | Parameter                     | Data record                                                                        |
| -------------------------- | ------------------ | ---------------------------------------- | ----------------------------- | ---------------------------------------------------------------------------------- |
| ReadDataByIdentifier       | 0x22 / 0x62        | —                                        | DID (2 bytes, repeatable)     | dataRecord per DID, supplied by RTE/SWC                                            |
| WriteDataByIdentifier      | 0x2E / 0x6E        | —                                        | DID (2 bytes)                 | dataRecord to write, applied via RTE/SWC                                           |
| RoutineControl             | 0x31 / 0x71        | start / stop / requestResults            | RID (2 bytes)                 | routineControlOptionRecord (req) / routineStatusRecord (resp), from RTE/SWC        |
| DiagnosticSessionControl   | 0x10 / 0x50        | session type                             | —                             | session parameter record (P2/P2* timing), response only                            |
| ReadDTCInformation         | 0x19 / 0x59        | report type (e.g. reportDTCByStatusMask) | DTCStatusMask / DTCMaskRecord | DTC + status records, or snapshot/extended data — supplied by **DEM**, not RTE/SWC |
| ClearDiagnosticInformation | 0x14 / 0x54        | —                                        | groupOfDTC (3 bytes)          | none — DEM purges matching entries                                                 |
| ControlDTCSetting          | 0x85 / 0xC5        | on / off                                 | —                             | optional DTCSettingControlOptionRecord — affects DEM's debouncing/status handling  |

Last three rows: identical message shape, data record content sourced from **DEM** rather than RTE/SWC — the DCM→DEM boundary of Section 2.1.

#### 1.3.2.1. Read/Write DID (Data Identifiers)

**ReadDataByIdentifier (0x22 / 0x62)** — reads one or more dataRecords identified by 2-byte DIDs. Multiple DIDs per request, including the same DID repeated; all dataRecords returned in one positive response, in order. Unsupported DID → negative response. [Clause 10.2]

**WriteDataByIdentifier (0x2E / 0x6E)** — writes a dataRecord at the location a DID identifies. Uses: configuration data (e.g. VIN), clearing non-volatile memory, resetting learned/adaptive values, option content. Write access may be restricted or security-locked; read-only DIDs must reject. Dynamically-defined DIDs not permitted. [Clause 10.7]

#### 1.3.2.2. RoutineControl (0x31 / response 0x71)

Executes a defined sequence of steps and returns results — memory erase, self-test, adaptive-value learning, overriding normal control strategy. More complex control than InputOutputControlByIdentifier, which covers simple/static output control. Routine referenced by a 2-byte routineIdentifier. [Clause 13.2.1]

- **Start routine (0x01)** — mandatory
- **Stop routine (0x02)** — optional
- **Request routine results (0x03)** — optional; exit status/results, e.g. data not sendable during execution due to performance limits

Allowed in the defaultSession. A non-default session is required for a **secured** routine (SecurityAccess first) and for a routine that must be **stopped actively by the client**; routines running instead of the normal operating code may need a specific session started first. [Table 23 footnote e; Clause 13.2.1.2]

#### 1.3.2.3. DiagnosticSessionControl (0x10 / response 0x50)

Switches the server between diagnostic sessions, each enabling a different set of services/functionality and potentially different timing parameters. Exactly one session active at a time. [Clause 9.2.1]

- **defaultSession (0x01)** — active at power-up; no timeout handling, no TesterPresent required
- **programmingSession (0x02)** — flashing/reprogramming
- **extendedDiagnosticSession (0x03)** — services for adjusting functions such as idle speed or CO value, plus services not tied to adjustment (the timed services of Table 23)
- **safetySystemDiagnosticSession (0x04)** — safety-related diagnostics
- **0x40-0x5F** vehicleManufacturerSpecific, **0x60-0x7E** systemSupplierSpecific

Table 23 gates services on default vs **non-default**, not on extendedDiagnosticSession: SecurityAccess, CommunicationControl, ControlDTCSetting and LinkControl are available in any non-default session; RoutineControl is available in the defaultSession (1.3.2.2). [Table 23]

programmingSession run in boot software is left only via ECUReset (0x11), DiagnosticSessionControl to defaultSession, or session-layer timeout; on the latter two the server restarts valid application software if present. [Table 25]

**Keeping a session alive.** Non-default sessions are tied to a diagnostic session timer the client must keep active; TesterPresent (0x3E) is sent periodically *"or in case of the absence of other diagnostic services"*. ISO 14229-1 does not define the timer, deferring it to the data-link implementation specifications. [Table 23; Clause 9.6.1]

**Session transitions** (Figure 7):

| Transition                                                       | Server behaviour                                                                                                                                                                                                                                                                           |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| defaultSession → defaultSession                                  | Complete re-initialization; reset every setting and control activated during the session. Long-term changes in non-volatile memory unaffected.                                                                                                                                             |
| defaultSession → any non-default session                         | Stop only the ResponseOnEvent (0x86) events configured during the defaultSession.                                                                                                                                                                                                          |
| non-default → non-default (including re-requesting the same one) | Stop all ResponseOnEvent events. **Re-lock security**, resetting functionality that depended on it (e.g. active inputOutputControl of a DID). Keep everything else the new session supports: periodic scheduler stays active; CommunicationControl and ControlDTCSetting states untouched. |
| non-default → defaultSession                                     | Stop all ResponseOnEvent events. Re-lock security. Terminate functionality the defaultSession does not support (periodic scheduler, output control). **Reset** CommunicationControl and ControlDTCSetting states.                                                                          |

Asymmetry: non-default → non-default *preserves* CommunicationControl and ControlDTCSetting state; → defaultSession *resets* it. [Clause 9.2.1, Figure 7]

*Caveat:* Figure 7 stops all ResponseOnEvent events on transition to the defaultSession; Clause 9.10.1 rule f states events previously active in the defaultSession "shall be re-activated". Confirm against the OEM specification. [Clause 9.2.1 Figure 7 vs. 9.10.1 rule f]

## 2. UDS in the AUTOSAR Architecture: DCM and DEM

UDS (ISO 14229) itself only defines the diagnostic *protocol* — the services, request/response formats, and behavior. In an AUTOSAR Classic Platform ECU, that protocol is implemented by two Basic Software (BSW) modules that work together:

- **DCM (Diagnostic Communication Manager)** — handles the tester-facing UDS services (sessions, security, DID read/write, routines, etc.)
- **DEM (Diagnostic Event Manager)** — handles fault/event storage (DTCs, freeze frames, extended data) generated by the application

### 2.1 Where DCM and DEM sit in the AUTOSAR architecture

Both DCM and DEM are BSW modules that live in the **Services Layer**, below the RTE and above the ECU Abstraction/MCAL layers — but they belong to **different functional groups** within that layer:

- **DCM is in Communication Services**, alongside COM, PduR, and the transport modules (CanTp/CanIf, SoAd for DoIP) — confirmed by the Dcm module's own specification (Figure 1.2, "Position of the Dcm module in AUTOSAR Architecture"). [AUTOSAR CP SWS Diagnostic Communication Manager]
- **DEM is in System Services**, alongside modules like EcuM, ComM, BswM, Det, and Dlt. [AUTOSAR CP SWS Diagnostic Event Manager]
- **NvM (used by DEM to persist event data) is in Memory Services**, a separate functional group from both.

![DCM and DEM in the AUTOSAR layered architecture](autosar-dcm-dem.svg)

- DCM sits between the diagnostic tester (via the communication stack: PduR, CanTp/CanIf, or DoIP/SoAd) and the rest of the ECU, translating UDS requests into internal calls.
- DEM sits between the application layer (SWCs with monitor functions that detect faults) and NvM (to persist event data), and it exposes DTC/event data to DCM on request.
- DCM and DEM call each other directly (`Dem_Dcm*` APIs) for services like ReadDTCInformation (0x19), ClearDiagnosticInformation (0x14), and ControlDTCSetting (0x85).

### 2.2 DCM (Diagnostic Communication Manager)

**DCM** consists of 3 submodules: **DSL** (Diagnostic Session Layer), **DSD** (Diagnostic Service Dispatcher), and **DSP** (Diagnostic Service Processing).

#### 2.2.1 DCM submodules

- **DSL (Diagnostic Session Layer)** — Manages the diagnostic buffer (Rx/Tx), communicates with PduR for transport, tracks session and security state, and works with ComM to enforce protocol timing (P2/P2*). It is the entry/exit point for diagnostic messages.
- **DSD (Diagnostic Service Dispatcher)** — Receives the incoming request from DSL, validates the service ID (SID) and whether it's supported/allowed in the current session and security level, dispatches it to DSP, tracks execution progress, and forwards the resulting positive/negative response back to DSL.
- **DSP (Diagnostic Service Processing)** — Implements the actual service-specific logic (e.g. ReadDataByIdentifier, WriteDataByIdentifier, RoutineControl, ReadDTCInformation). It reaches into RTE/SWCs for application data and into DEM for DTC/event data, then assembles the response.

#### 2.2.2 DCM basic call flow 

![DCM internal submodules and call flow](autosar-dcm-relation.svg)

1. Tester sends a UDS request → arrives via the communication stack → **PduR** hands it to **DSL**.
2. **DSL** buffers the message and notifies **DSD** of the new request.
3. **DSD** validates the SID plus session/security permissions, then dispatches to **DSP**.
4. **DSP** executes the requested service — for DID or routine services it may call RTE/SWCs; for DTC-related services (0x19, 0x14, 0x85) it calls **DEM** (e.g. `Dem_GetEventStatus`, `Dem_ClearDTC`, `Dem_DcmReadDataOfDTCByEvent`).
5. The result (or NRC) flows back: DSP → DSD → DSL → PduR → Tester.

### 2.3 DEM (Diagnostic Event Manager)

*Note: unlike Section 1 and the DCM submodule split in 2.2 (both traceable to ISO 14229-1 and the AUTOSAR Dcm SWS respectively), DEM has no formal "submodule" breakdown in its own AUTOSAR specification. The groupings below are a functional/informal organization of responsibilities that the AUTOSAR CP SWS Diagnostic Event Manager actually specifies (debouncing/fault confirmation, event memory, freeze frame/extended data, aging/healing, NvM persistence, and the Dcm-facing interface) — not literal named sub-blocks the way DSL/DSD/DSP are for DCM. See [4] for the primary source and [5] for a secondary source confirming the aging/healing terminology.*

**DEM** is not formally split into named "submodules" the way DCM is, but is functionally organized into these internal responsibilities:

- **Debouncing** — confirms whether a raw monitor result becomes an actual fault, using counter-based or monitor-internal debounce algorithms.
- **Event Memory Manager** — maintains DTC status bits, event priority, and aging/healing cycle counters.
- **Freeze Frame / Extended Data Manager** — captures and stores snapshot data (e.g. mileage, RPM, temperature) and extended data records at the time of a fault.
- **DTC / Event Status Manager** — handles DTC groups, event combination (combination on storage vs. retrieval), and DTC suppression.
- **Callback / Notification Interface** — notifies other modules (FIM, DCM, SWCs) when an event/DTC status changes.
- **NvM Interface** — persists event memory data to non-volatile memory so it survives power cycles.
- **Dcm Interface** — serves DTC status, freeze frame, and extended data back to DCM when the tester requests it.

### 2.3.1 DEM basic call flow 

![DEM internal architecture and call flow](autosar-dem-relation.svg)

1. A **SWC monitor** detects a fault condition and reports it via **RTE** (`Dem_SetEventStatus` / `Dem_ReportErrorStatus`).
2. DEM's **debouncing** logic confirms the fault before treating it as failed.
3. The **Event Memory Manager** updates the DTC/event status and, if configured, the **Freeze Frame / Extended Data Manager** captures a snapshot.
4. The **Callback/Notification Interface** informs **FIM** (Function Inhibition Manager) so dependent functions can be inhibited, and persists the entry via the **NvM Interface**.
5. When the tester later requests fault data (e.g. UDS service 0x19 ReadDTCInformation), **DCM** calls into DEM's **Dcm Interface**, which returns the current DTC status, freeze frame, and extended data for DCM to format into the UDS response.

# References

[1] ISO 14229-1:2013(E), *Road vehicles — Unified diagnostic services (UDS) — Part 1: Specification and requirements*, ISO/TC 22/SC 3. Authoritative source for Section 1: Clause 1 Scope; Introduction and Table 1 (OSI layer allocation); Clause 4 Conventions with Figure 1 "The services and the protocol" (the service/protocol, A_SDU/A_PDU distinction) and Clause 3.2 Abbreviated terms; Clause 6.1 General (client-server model, six service primitives, Figures 3-4); Clauses 6.3.2 – 6.3.4 (service primitive formats), 6.4 Service data unit specification (A_SDU mandatory parameters and the optional A_AE), 7.2 Protocol data unit specification (A_PDU), 7.3 Application protocol control information (A_PCI, SI, NR_SI), 7.4 with Table 3 (negative response A_PDU), 7.5.5 (server pseudo-code, A_PDU dotted-path notation) and Clause 8 Service description conventions (Table 8 A_PDU parameter conventions; Tables 9 and 10 request A_PDU definitions; Table 13 sub-function conventions); Clause 9 Diagnostic and Communication Management functional unit (Table 22 service list, Table 23 SIDs and session availability, and the per-service descriptions in 9.2.1 – 9.11.1); Clause 13.2 RoutineControl. Note: this document does not mention DEM — it defines the DTC/status-byte protocol data model only, not how a server implements storage internally. Clause numbering differs from the earlier ISO/DIS 14229-1:2011, where the Diagnostic and Communication Management functional unit was Clause 10.

[2] AUTOSAR Classic Platform, *Specification of Diagnostic Communication Manager (Dcm)*, AUTOSAR CP Release R20-11 — Figure 1.2 "Position of the Dcm module in AUTOSAR Architecture" (Communication Services placement); submodule structure (DSL/DSD/DSP); TOC entry "Interface DSP - DEM (service 0x19, 0x14, 0x85)" (confirms the DCM→DEM call for these three UDS services).
https://www.autosar.org/fileadmin/standards/R20-11/CP/AUTOSAR_SWS_DiagnosticCommunicationManager.pdf

[3] Krishna, "Diagnostic Communication Manager | DCM | Diagnostics in AUTOSAR," autosartutorials.com — independent confirmation that "DCM ... lies in Communication Services block."
https://autosartutorials.com/diagnostic-communication-manager-dcm/

[4] AUTOSAR Classic Platform, *Specification of Diagnostic Event Manager (Dem)*, AUTOSAR CP Release R23-11 — primary source for Dem's functional responsibilities (event status/debouncing via `Dem_SetEventStatus`, freeze frame via `Dem_PrestoreFreezeFrame`/`Dem_GetEventFreezeFrameData`, DTC clearing via `Dem_ClearDTC`), System Services placement, and the Dcm-facing interface.
https://www.autosar.org/fileadmin/standards/R23-11/CP/AUTOSAR_CP_SWS_DiagnosticEventManager.pdf

[5] "Diagnostic Stack in AUTOSAR," automotivevehicletesting.com — secondary source confirming "the DCM resides in the Communication Services layer, DEM in the System Services layer" and the aging/healing terminology used in Section 2.3.
https://automotivevehicletesting.com/autosar/diagnostic-stack-in-autosar/
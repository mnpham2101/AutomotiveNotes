# ISO 14229-1 (UDS) — Quick Overview

This is the ISO 14229-1 standard (Unified Diagnostic Services, UDS), which defines the application-layer protocol used for diagnostic communication with electronic control units (ECUs) in vehicles. It specifies the request/response message formats, service IDs, and behavioral rules for diagnostic services like reading/writing data, running routines, controlling communication, and managing security access — independent of the underlying transport (CAN, LIN, Ethernet, etc.).

Below are three key services covered in the standard.

## 1. Diagnostic Service Requirements defined by ISO-14229

### 1.1. General

**Client-server model.** ISO 14229-1 is built around a **client-server** relationship: a diagnostic tester (the **client**) — usually off-board test equipment, though it can be on-board — controls diagnostic functions in an on-vehicle ECU (the **server**, e.g. an engine management system, ABS, or automatic gearbox). The client requests a diagnostic service, and the server performs it and sends response data back. The client role and server role are independent of the underlying data link, and more than one client can exist in the same vehicle system. [ISO 14229-1:2013, Clause 1 Scope; Clause 6.1 General]

**Six service primitives.** For each diagnostic service, the standard defines six "service primitives" that describe how data moves between the client/server applications and the diagnostics application layer:

1. **Request** — client passes data about a requested service to the diagnostics application layer
2. **Request-confirmation** — confirms to the client that the request data was fully transferred to the server
3. **Indication** — diagnostics application layer passes the request data to the server function
4. **Response** — server passes the requested service's response data (positive or negative) to the diagnostics application layer
5. **Response-confirmation** — confirms to the server that the response data was fully transferred to the client
6. **Confirmation** — diagnostics application layer passes the response data to the client function

### 1.1.1 Mapping the communication stack onto the OSI model

**Position in the OSI model.** The standard maps diagnostic communication onto the seven-layer OSI Basic Reference Model (ISO 7498-1 / ISO/IEC 10731): **Unified diagnostic services occupy layer 7 (application layer)**, while the underlying data link (CAN, LIN, FlexRay, Ethernet, etc.) provides **communication services across layers 1–6**. This is what makes UDS transport-independent — the same service definitions apply regardless of which network carries them. The standard's own layer allocation names ISO 14229-2 at the session layer (5), and ISO 15765-2 / ISO 10681-2 / ISO 13400-2 / ISO 17987-2 jointly at *both* the transport (4) and network (3) layers. [ISO 14229-1:2013, Introduction and Table 1]

The ISO document does not go further than that — it does not itself specify where individual AUTOSAR CAN-stack modules (PduR, CanIf, CanDrv, CanTp) sit on the OSI model. 

The mapping below is therefore drawn from general AUTOSAR/ISO 15765 architecture knowledge, not from ISO 14229-1 itself.

![UDS/AUTOSAR communication stack mapped onto the OSI reference model](../asset/autosar-uds-osi-mapping.svg)

A few clarifications on that mapping:

- **CanIf → Data Link** and **CanDrv → Physical** are reasonable, commonly used mappings.
- **CanTp → Transport** is correct, but incomplete: ISO 15765-2, which CanTp implements, is titled *"Transport protocol **and network layer** services"* — so CanTp arguably covers Layer 3 as well as Layer 4, rather than Layer 4 alone.
- **PduR → Network layer** is the weakest part of the mapping. PduR is a routing/multiplexing dispatcher between BSW modules (DCM, CanTp, COM), not an OSI Layer-3 entity — it does not perform addressing or routing across physical networks the way a true network-layer protocol does. It is commonly drawn near Layer 3/4 for convenience, but that placement is an approximation rather than an architectural fact.
- Layers 5 and 6 (Session, Presentation) have no dedicated AUTOSAR module; the diagnostic "session" concept (defaultSession, programmingSession, etc.) is itself a Layer-7 UDS concept (DiagnosticSessionControl), not an OSI Layer-5 session.

### 1.2 Services

ISO 14229-1 groups its services into **functional units**, one per clause — **26 services in total**:

| Functional unit                          | Clause | Services | What the group is for                                        |
| ---------------------------------------- | ------ | -------- | ------------------------------------------------------------ |
| Diagnostic and Communication Management  | 9      | 10       | Manages the diagnostic conversation itself: which session is active, whether the server is unlocked, whether the tester is still connected, and how communication and DTC recording behave. |
| Data Transmission                        | 10     | 7        | Reads and writes live data, by identifier or by memory address. |
| Stored Data Transmission                 | 11     | 2        | Reads and clears stored fault information (DTCs, snapshots).  |
| InputOutput Control                      | 12     | 1        | Overrides an input signal or forces an actuator output.       |
| Routine                                  | 13     | 1        | Starts/stops a server-resident routine and fetches its results. |
| Upload Download                          | 14     | 5        | Negotiates and executes bulk data/file transfer — the basis of flash programming. |

Note the clause numbering shifted between drafts: the Diagnostic and Communication Management functional unit is Clause 9 in ISO 14229-1:2013, but was Clause 10 in the earlier ISO/DIS 14229-1:2011.

The full service list follows. The last column quotes the opening line of each service's own "Service description" subclause in ISO 14229-1:2013, which is the standard's own one-sentence definition of the service.

| Service (SID)                                | What it does                                                                                                                                                                                                                                                                 | ISO 14229-1:2013 — opening line of the service description                                                                                                                                                                       |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Diagnostic and Communication Management — Clause 9** |                                                                                                                                                                                                                                                                    |                                                                                                                                                                                                                                      |
| DiagnosticSessionControl (0x10)              | Enables a diagnostic session in the server. Each session enables a specific set of services and functionality — *which* set is defined by the OEM, not by ISO. Exactly one session is active at a time, and the server starts in defaultSession at power-up.                   | *"The DiagnosticSessionControl service is used to enable different diagnostic sessions in the server(s)."* [9.2.1]                                                                                                                   |
| ECUReset (0x11)                              | Forces the server to reset itself, with the resetType parameter selecting the kind of reset (hard, key-off-on, soft, rapid power shutdown). The positive response is sent before the reset executes, and the server comes back in defaultSession.                              | *"The ECUReset service is used by the client to request a server reset."* [9.3.1]                                                                                                                                                    |
| SecurityAccess (0x27)                        | Unlocks data and services restricted for security, emissions or safety reasons, via a seed-and-key exchange: the client requests a seed, returns the matching key, and the server unlocks if the key is valid. Only one security level is active at a time.                    | *"The purpose of this service is to provide a means to access data and/or diagnostic services, which have restricted access for security, emissions, or safety reasons."* [9.4.1]                                                     |
| CommunicationControl (0x28)                  | Switches transmission and/or reception of certain classes of messages on or off in the server (e.g. normal application communication) — used to quieten the bus for diagnostics.                                                                                               | *"The purpose of this service is to switch on/off the transmission and/or the reception of certain messages of (a) server(s) (e.g. application communication messages)."* [9.5.1]                                                     |
| TesterPresent (0x3E)                         | Signals that the client is still connected, so previously activated services and communication remain active. This is what holds a server in a non-default session instead of letting it time out back to defaultSession.                                                      | *"This service is used to indicate to a server (or servers) that a client is still connected to the vehicle and that certain diagnostic services and/or communication that have been previously activated are to remain active."* [9.6.1] |
| AccessTimingParameter (0x83)                 | Reads and changes the default communication timing parameters for as long as the link is active. Offers four modes: read extended set, read currently active, set to given values, set to default. Timings reset to default on any session change.                             | *"The AccessTimingParameter service is used to read and change the default timing parameters of a communication link for the duration this communication link is active."* [9.7.1]                                                    |
| SecuredDataTransmission (0x84)               | Transmits a diagnostic message — or an external-protocol message — in secured mode, protected by cryptographic methods against third-party attack. A security sub-layer above the application layer performs the encryption/decryption; secured links are point-to-point only. | *"The purpose of this service is to transmit data that is protected against attacks from third parties - which could endanger data security."* [9.8.1.1]                                                                              |
| ControlDTCSetting (0x85)                     | Stops or resumes the updating of DTC status bits in the server. It only freezes the status bits: it does not switch off fault monitoring, and is not intended to disable failsoft strategies.                                                                                  | *"The ControlDTCSetting service shall be used by a client to stop or resume the updating of DTC status bits in the server(s)."* [9.9.1]                                                                                              |
| ResponseOnEvent (0x86)                       | Sets up the server to execute a nominated diagnostic service automatically whenever a specified event occurs, and starts/stops that event logic. Can be set up in any session including defaultSession, and does not require TesterPresent to stay active.                     | *"The ResponseOnEvent service requests a server to start or stop transmission of responses on a specified event."* [9.10.1]                                                                                                          |
| LinkControl (0x87)                           | Reconfigures the data link — typically to a higher baudrate — to gain bus bandwidth for diagnostics such as programming. The transition is two-stage (verify, then transition) and applies only in a non-default session.                                                      | *"The LinkControl service is used to control the communication between the client and the server(s) in order to gain bus bandwidth for diagnostic purposes (e.g., programming)."* [9.11.1]                                            |
| **Data Transmission — Clause 10**            |                                                                                                                                                                                                                                                                              |                                                                                                                                                                                                                                      |
| ReadDataByIdentifier (0x22)                  | Reads the current value of one or more data records, each named by a 2-byte DID. The workhorse read service — VIN, part numbers, sensor values, status words. The server may cap how many DIDs one request can carry.                                                          | *"The ReadDataByIdentifier service allows the client to request data record values from the server identified by one or more dataIdentifiers."* [10.2.1]                                                                              |
| ReadMemoryByAddress (0x23)                   | Reads raw memory by start address and length rather than by DID. The addressAndLengthFormatIdentifier byte declares how many bytes the address and size fields each use.                                                                                                       | *"The ReadMemoryByAddress service allows the client to request memory data from the server via provided starting address and size of memory to be read."* [10.3.1]                                                                    |
| ReadScalingDataByIdentifier (0x24)           | Reads the *scaling* metadata for one DID — data type, resolution, offset, unit, validity — rather than the value itself, so a tester can interpret raw bytes without a hard-coded description file.                                                                            | *"The ReadScalingDataByIdentifier service allows the client to request scaling data record information from the server identified by a dataIdentifier."* [10.4.1]                                                                     |
| ReadDataByPeriodicIdentifier (0x2A)          | Schedules the server to transmit data records repeatedly (slow / medium / fast rate, or stopSending) instead of one response per request. Uses 1-byte periodic DIDs, which are the low byte of the reserved 0xF2XX DID range.                                                  | *"The ReadDataByPeriodicIdentifier service allows the client to request the periodic transmission of data record values from the server identified by one or more periodicDataIdentifiers."* [10.5.1]                                 |
| DynamicallyDefineDataIdentifier (0x2C)       | Builds a new DID at runtime by grouping existing DIDs or memory ranges into one superset, which can then be read in a single 0x22 or 0x2A request — fewer round trips when logging several signals.                                                                            | *"The DynamicallyDefineDataIdentifier service allows the client to dynamically define in a server a data identifier that can be read via the ReadDataByIdentifier service at a later time."* [10.6.1]                                 |
| WriteDataByIdentifier (0x2E)                 | Writes a data record to the location named by a DID — e.g. programming a VIN, clearing non-volatile memory, resetting learned values, setting option content. Dynamically defined DIDs must not be used with it.                                                               | *"The WriteDataByIdentifier service allows the client to write information into the server at an internal location specified by the provided data identifier."* [10.7.1]                                                              |
| WriteMemoryByAddress (0x3D)                  | Writes raw bytes to a contiguous memory range given by address and size — the write counterpart of 0x23, used for calibration changes and clearing non-volatile memory.                                                                                                        | *"The WriteMemoryByAddress service allows the client to write information into the server at one or more contiguous memory locations."* [10.8.1]                                                                                      |
| **Stored Data Transmission — Clause 11**     |                                                                                                                                                                                                                                                                              |                                                                                                                                                                                                                                      |
| ClearDiagnosticInformation (0x14)            | Clears stored DTCs and their associated captured data for a DTC group. The server answers positively even when no DTCs were stored; in AUTOSAR this is served by DEM via `Dem_ClearDTC`.                                                                                       | *"The ClearDiagnosticInformation service is used by the client to clear diagnostic information in one or multiple servers' memory."* [11.2.1]                                                                                        |
| ReadDTCInformation (0x19)                    | Reads stored fault information: DTC counts and lists filtered by status mask, snapshot (freeze frame) records, extended data records, severity, permanent DTCs. By far the largest service — its behaviour is selected by ~20 sub-functions.                                   | *"This service allows a client to read the status of server resident Diagnostic Trouble Code (DTC) information from any server, or group of servers within a vehicle."* [11.3.1.1]                                                    |
| **InputOutput Control — Clause 12**          |                                                                                                                                                                                                                                                                              |                                                                                                                                                                                                                                      |
| InputOutputControlByIdentifier (0x2F)        | Substitutes an input signal or forces an actuator output, referenced by DID (returnControlToECU / resetToDefault / freezeCurrentState / shortTermAdjustment). Intended for simple, static overrides — complex control belongs in RoutineControl.                                | *"The InputOutputControlByIdentifier service is used by the client to substitute a value for an input signal, internal server function and/or force control to a value for an output (actuator) of an electronic system."* [12.2.1]   |
| **Routine — Clause 13**                      |                                                                                                                                                                                                                                                                              |                                                                                                                                                                                                                                      |
| RoutineControl (0x31)                        | Starts a routine, stops it, or requests its results, referenced by a 2-byte routineIdentifier. Typical uses: erase memory, check programming dependencies, run a self-test, reset adaptive data.                                                                               | *"The RoutineControl service is used by the client to execute a defined sequence of steps and obtain any relevant results."* [13.2.1]                                                                                                |
| **Upload Download — Clause 14**              |                                                                                                                                                                                                                                                                              |                                                                                                                                                                                                                                      |
| RequestDownload (0x34)                       | Negotiates a transfer *into* the server: the client states the data format, address and size; the server replies with the maxNumberOfBlockLength it will accept per TransferData block. Step 1 of a flash download.                                                            | *"The requestDownload service is used by the client to initiate a data transfer from the client to the server (download)."* [14.2.1]                                                                                                 |
| RequestUpload (0x35)                         | The mirror image of 0x34 — negotiates a transfer *out of* the server to the client, e.g. reading back a calibration area.                                                                                                                                                     | *"The RequestUpload service is used by the client to initiate a data transfer from the server to the client (upload)."* [14.3.1]                                                                                                     |
| TransferData (0x36)                          | Carries the actual payload blocks, in whichever direction the preceding 0x34/0x35 established. Each request carries a blockSequenceCounter (starting at 1, wrapping 0xFF→0x00) so a failed block can be retried unambiguously.                                                 | *"The TransferData service is used by the client to transfer data either from the client to the server (download) or from the server to the client (upload)."* [14.4.1]                                                               |
| RequestTransferExit (0x37)                   | Ends the transfer sequence and lets the server run its closing checks (e.g. checksum/CRC verification) before releasing the download/upload state.                                                                                                                             | *"This service is used by the client to terminate a data transfer between client and server (upload or download)."* [14.5.1]                                                                                                         |
| RequestFileTransfer (0x38)                   | The file-system alternative to 0x34/0x35 for servers that store data as files: opens a file for read or write, and can also delete files/directories or read file-system information. Data still moves via 0x36 and finishes with 0x37 (except for delete).                     | *"The requestFileTransfer service is used by the client to initiate a file data transfer from either the client to the server or from the server to the client (download or upload)."* [14.6.1]                                       |

[ISO 14229-1:2013, functional-unit overview tables — Table 22 (Clause 9.1), Table 141 (10.1), Table 249 (11.1), Table 351 (12.1), Table 377 (13.1), Table 392 (14.1) — and the per-service "Service description" subclauses cited row by row above]

### 1.3 Basic UDS Message

### 1.3.1 Message structure: A_SDU, A_PDU and the mandatory parameters

- **A_SDU** (Application layer **Service** Data Unit) — parameters passed across the service primitive, application ↔ application layer; never leaves the ECU. Figure 1: `SA, TA, TAtype, [parameter#1, parameter#2, …]`. [Clause 6.4]
- **A_PDU** (Application layer **Protocol** Data Unit) — "directly constructed from the A_SDU and the layer specific control information A_PCI"; what one application layer sends to its peer. Figure 1: `SA, TA, TAtype, `**`A_PCI`**`, [parameter#1, parameter#2, …]`. [Clause 7.2]

![ISO 14229-1 message structure: A_SDU vs A_PDU](../asset/uds-sdu-pdu-format.svg)

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

###  1.3.2. A_Data subsection in UDS message

Request = SID + optional sub-function + optional parameter + optional data record:

- **SID** (1 byte) — the service, e.g. `0x22` ReadDataByIdentifier
- **Sub-function** (1 byte, optional) — mode within the service, e.g. `0x01` = start routine for RoutineControl
- **Parameter** (1-3 bytes, optional) — DID, RID, or DTC group/mask
- **Data record** (variable length, optional) — payload written, or option data

Positive response: request SID + `0x40`, echoed parameters, data record. Negative response: fixed 3 bytes — `0x7F`, request SID, 1-byte NRC. [Clause 7.4, Table 3]

![Common UDS message format and field mapping to DCM/DEM services](../asset/full-UDS-msg-format.svg)

#### 1.3.2.1. The sub-function byte

![Sub-function byte structure — bit 7 is SPRMIB, bits 6–0 carry the sub-function value](../uds/asset/uds-slide-subfunction.svg)

- Present only in services that define one — always **exactly 1 byte, 8 bits**.
- Bit 7 = **SPRMIB**, suppressPosRspMsgIndicationBit; bits 6–0 = the sub-function value, 0x00–0x7F.
- Both SPRMIB values must be supported for every sub-function value the server supports.

`[Clause 8.2.2, Tables 11 and 14]`

> note: There is no general server response behaviour available for request messages without sub-function parameter (7.5.4.1).

## 2. UDS in the AUTOSAR Architecture: DCM and DEM

UDS (ISO 14229) itself only defines the diagnostic *protocol* — the services, request/response formats, and behavior. In an AUTOSAR Classic Platform ECU, that protocol is implemented by two Basic Software (BSW) modules that work together:

- **DCM (Diagnostic Communication Manager)** — handles the tester-facing UDS services (sessions, security, DID read/write, routines, etc.)
- **DEM (Diagnostic Event Manager)** — handles fault/event storage (DTCs, freeze frames, extended data) generated by the application

### 2.1 Where DCM and DEM sit in the AUTOSAR architecture

Both DCM and DEM are BSW modules that live in the **Services Layer**, below the RTE and above the ECU Abstraction/MCAL layers — but they belong to **different functional groups** within that layer:

- **DCM is in Communication Services**, alongside COM, PduR, and the transport modules (CanTp/CanIf, SoAd for DoIP) — confirmed by the Dcm module's own specification (Figure 1.2, "Position of the Dcm module in AUTOSAR Architecture"). [AUTOSAR CP SWS Diagnostic Communication Manager]
- **DEM is in System Services**, alongside modules like EcuM, ComM, BswM, Det, and Dlt. [AUTOSAR CP SWS Diagnostic Event Manager]
- **NvM (used by DEM to persist event data) is in Memory Services**, a separate functional group from both.

![DCM and DEM in the AUTOSAR layered architecture](../asset/autosar-dcm-dem.svg)

- DCM sits between the diagnostic tester (via the communication stack: PduR, CanTp/CanIf, or DoIP/SoAd) and the rest of the ECU, translating UDS requests into internal calls.
- DEM sits between the application layer (SWCs with monitor functions that detect faults) and NvM (to persist event data), and it exposes DTC/event data to DCM on request.
- DCM and DEM call each other directly (`Dem_Dcm*` APIs) for services like ReadDTCInformation (0x19), ClearDiagnosticInformation (0x14), and ControlDTCSetting (0x85).

### 2.2 DCM (Diagnostic Communication Manager)

**DCM** consists of 3 submodules: **DSL** (Diagnostic Session Layer), **DSD** (Diagnostic Service Dispatcher), and **DSP** (Diagnostic Service Processing).

#### 2.2.1 DCM submodules

- **DSL (Diagnostic Session Layer)** — Manages the diagnostic buffer (Rx/Tx), communicates with PduR for transport, tracks session and security state, and works with ComM to enforce protocol timing (P2/P2*). It is the entry/exit point for diagnostic messages.
- **DSD (Diagnostic Service Dispatcher)** — Receives the incoming request from DSL, validates the service ID (SID) and whether it's supported/allowed in the current session and security level, dispatches it to DSP, tracks execution progress, and forwards the resulting positive/negative response back to DSL.
- **DSP (Diagnostic Service Processing)** — Implements the actual service-specific logic (e.g. ReadDataByIdentifier, WriteDataByIdentifier, RoutineControl, ReadDTCInformation). It reaches into RTE/SWCs for application data and into DEM for DTC/event data, then assembles the response.

#### 2.2.2 DCM relationship with other components

![DCM internal submodules and relationship with other components](../asset/autosar-dcm-relation.svg)

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

### 2.3.1 DEM relationship with other components

![DEM internal architecture and relationship with other components](../asset/autosar-dem-relation.svg)

1. A **SWC monitor** detects a fault condition and reports it via **RTE** (`Dem_SetEventStatus` / `Dem_ReportErrorStatus`).
2. DEM's **debouncing** logic confirms the fault before treating it as failed.
3. The **Event Memory Manager** updates the DTC/event status and, if configured, the **Freeze Frame / Extended Data Manager** captures a snapshot.
4. The **Callback/Notification Interface** informs **FIM** (Function Inhibition Manager) so dependent functions can be inhibited, and persists the entry via the **NvM Interface**.
5. When the tester later requests fault data (e.g. UDS service 0x19 ReadDTCInformation), **DCM** calls into DEM's **Dcm Interface**, which returns the current DTC status, freeze frame, and extended data for DCM to format into the UDS response.

# References

[1] ISO 14229-1:2013(E), *Road vehicles — Unified diagnostic services (UDS) — Part 1: Specification and requirements*, ISO/TC 22/SC 3. Authoritative source for Section 1: Clause 1 Scope; Introduction and Table 1 (OSI layer allocation); Clause 4 Conventions with Figure 1 "The services and the protocol" (the service/protocol, A_SDU/A_PDU distinction) and Clause 3.2 Abbreviated terms; Clause 6.1 General (client-server model, six service primitives, Figures 3-4); Clauses 6.3.2 – 6.3.4 (service primitive formats), 6.4 Service data unit specification (A_SDU mandatory parameters and the optional A_AE), 7.2 Protocol data unit specification (A_PDU), 7.3 Application protocol control information (A_PCI, SI, NR_SI), 7.4 with Table 3 (negative response A_PDU), 7.5.5 (server pseudo-code, A_PDU dotted-path notation) and Clause 8 Service description conventions (Table 8 A_PDU parameter conventions; Tables 9 and 10 request A_PDU definitions; Table 13 sub-function conventions); and the six functional units with their overview tables and per-service "Service description" subclauses — Clause 9 Diagnostic and Communication Management (Table 22 service list, Table 23 SIDs and session availability, descriptions 9.2.1 – 9.11.1), Clause 10 Data Transmission (Table 141, descriptions 10.2.1 – 10.8.1), Clause 11 Stored Data Transmission (Table 249, descriptions 11.2.1 – 11.3.1.1), Clause 12 InputOutput Control (Table 351, description 12.2.1), Clause 13 Routine (Table 377, description 13.2.1) and Clause 14 Upload Download (Table 392, descriptions 14.2.1 – 14.6.1). Note: this document does not mention DEM — it defines the DTC/status-byte protocol data model only, not how a server implements storage internally. Clause numbering differs from the earlier ISO/DIS 14229-1:2011, where the Diagnostic and Communication Management functional unit was Clause 10.

[2] AUTOSAR Classic Platform, *Specification of Diagnostic Communication Manager (Dcm)*, AUTOSAR CP Release R20-11 — Figure 1.2 "Position of the Dcm module in AUTOSAR Architecture" (Communication Services placement); submodule structure (DSL/DSD/DSP); TOC entry "Interface DSP - DEM (service 0x19, 0x14, 0x85)" (confirms the DCM→DEM call for these three UDS services).
https://www.autosar.org/fileadmin/standards/R20-11/CP/AUTOSAR_SWS_DiagnosticCommunicationManager.pdf

[3] Krishna, "Diagnostic Communication Manager | DCM | Diagnostics in AUTOSAR," autosartutorials.com — independent confirmation that "DCM ... lies in Communication Services block."
https://autosartutorials.com/diagnostic-communication-manager-dcm/

[4] AUTOSAR Classic Platform, *Specification of Diagnostic Event Manager (Dem)*, AUTOSAR CP Release R23-11 — primary source for Dem's functional responsibilities (event status/debouncing via `Dem_SetEventStatus`, freeze frame via `Dem_PrestoreFreezeFrame`/`Dem_GetEventFreezeFrameData`, DTC clearing via `Dem_ClearDTC`), System Services placement, and the Dcm-facing interface.
https://www.autosar.org/fileadmin/standards/R23-11/CP/AUTOSAR_CP_SWS_DiagnosticEventManager.pdf

[5] "Diagnostic Stack in AUTOSAR," automotivevehicletesting.com — secondary source confirming "the DCM resides in the Communication Services layer, DEM in the System Services layer" and the aging/healing terminology used in Section 2.3.
https://automotivevehicletesting.com/autosar/diagnostic-stack-in-autosar/
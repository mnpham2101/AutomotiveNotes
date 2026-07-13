# Minh Pham

Hochiminh City, Vietnam
Phone: 096.462.7117 | Email: <mnpham1986@gmail.com>
[LinkedIn](https://www.linkedin.com/in/minh-pham-b4b162127/) | [Website](https://freewindcode.com/) | [GitHub](https://github.com/mnpham2101/AutomotiveNotes/tree/main/doc/KnowledgeBase)

---

## Objective

Looking for a career as C/C++ Developer, Firmware Engineer.

---

## Education

**California Polytechnic University, Pomona** — March 2012
*BS – Electrical & Computer Engineering*

**University of North Florida** — 2014–2015
*BS – Electrical & Computer Engineering*

---

## Certifications

- IEEE Wireless Communications Professional — certification earned in Nov 2018
- HackerRank Problem Solving (Basic), LeetCode

---

## Domain-Specific Background

- **Automotive Software Development:** familiar with AUTOSAR Classic and AUTOSAR Adaptive.
- **Android Platform:** Android Binder as IPC/RPC method; Looper / MsgQueue / Handler for threading and communication.
- **Advanced knowledge of 5G:** focus on MAC protocols.
- **Embedded systems:** understanding of **SPI, I2C, UART, CAN, LIN** protocols, boot procedure, interrupts, and the **AUTOSAR** platform.
- **Software QC testing:** design and perform manual and automation tests on 5G products. Familiar with test process and the V-Model.

---

## Software Tools

- Agentic AI
- C/C++ programming (C++17), Google Unit Test, Qt Framework
- Slint, Rust
- Flutter, Flutter Engine
- C#, Ranorex Test Framework
- Python, Robot Framework, QXDM and Wireshark

---

## Professional Experience

### FPT Software — Danang, Vietnam
**Senior Architect, Technical Lead** · Jan 2024 – Present

**Trained on AUTOSAR embedded know-how**

Self-training from FPT's internal knowledge base, covering the following skills:

- Configure NVIC interrupt priorities and Icu/Gpt input-capture channels to keep interrupt latency within the timing budget for time-critical signals.
- Debug bus-fault and hard-fault issues: decode CFSR, BFAR, and HFSR registers and correlate against the exception stack frame to confirm the offending peripheral access.

**Team management**

- Perform the roles of Senior Architect and Technical Lead. Manage tickets and project progress; work as Agile master.
- Review architecture design and system design. Review functional and non-functional features for ECUs.
- Review code before submission to customers, ensuring compliance with best practice and testability.
- Proactively make technical presentations, engage in technical discussion with the customer to clarify requirements, and find the best solution.

**Programming tasks**

- Demo HMI development application for Vehicle Infovista *(6 months)*
  - Implement HMI features. Fluent in Dart. Implement common components; design data flow between components and backend. Implement gRPC service in Dart to handle requests to/from backend.
  - Implement Bluetooth using the BlueZ Dart package.
  - Support implementing a Wi-Fi service in C++, running as a daemon service in Linux.
  - Implement an Observer class to watch for changes in peripherals and service notifications from the Linux kernel, such as availability of media service, Wi-Fi network, and connected devices.
  - Use the flutter-embedded-linux engine to support multi-window front-end applications.
  - Write CMake to build multiple binaries for different applications (Media, Wi-Fi, Bluetooth). Create custom CMake functions to better manage build scripts and dependencies for each application/module.
  - Write C++ backend logic to handle requests when a user clicks a front-end component and opens a new application running in a different process.
- Migrate backend library, removing Qt dependency *(6 months)*
  - Migrate Qt-dependent code to non-Qt code using C++ and Rust.
  - Implement a custom protocol for CNC machines: ensure full duplex, multiple access, encryption, and message integrity.
  - Use the Asio library to replace QNetwork; KDBinding to replace Qt signal/slot; SQLiteCpp to replace Qt SQL; `std::variant` and other C++20 containers to replace Qt containers and Qt-defined data types.
  - Implement custom helper functions for commonly used logic such as parsing message headers and converting/checking data types.
  - Use variadic template functions and spdlog to replace Qt logging.
  - Implement gTests for all production code, ensuring above 84% coverage for C0, C1, and C2. Use parameterized tests to cover a wide range of input data for the same test scenarios.
- Implement Slint components *(3 months)*
  - Define Slint custom buttons and custom layouts. Adhere to declarative coding style. Follow strict customer coding rules to create well-maintainable components.
  - Implement Rust logic to drive the Slint components.

### TMA Solutions — Hochiminh City, Vietnam
**Senior Software Engineer** · Oct 2023 – Dec 2024

- Involved in software development for the Distributed Unit (DU).

**Programming tasks**

- Resolve memory leak issues.
- Implement RLC for both AM/UM modes and MAC counters according to 3GPP and O-RAN requirements.
- Implement abnormal behavior handling during cell delete, involving the NG and F1AP interfaces.
- Implement UL power control algorithm and propose a UL scheduling algorithm based on both the Power Headroom Report and UL power control.
- Implement automation tests using the Robot Framework.

**Team coworking**

- Perform code review for team members before merge, ensuring clean-code practice.
- Provide 5G and *clean code* training.

### Rikkeisoft — Hanoi, Vietnam
**Junior Software Engineer at AllianceBernstein** · July 2022 – Oct 2023

- Involved in software maintenance and new feature delivery for AllianceBernstein.

**Programming tasks**

- Designed and implemented a new daemon to process account balances at end of day based on the status of data in SQL Server.
- Designed and implemented a new service handler to process new transaction requests sent to a SOAP server. Integrated the service handlers with the gSOAP library.
- Programmed automation code using C# and the Ranorex framework to read test data from Excel files, invoke tested programs, and output test results.
- Implemented stored procedures and SQL query C++ classes to send requests to the SQL database.

**Software maintenance tasks**

- Monitored servers running Control-M jobs for failed jobs; debugged errors by analyzing logs and code to find root causes.

### LGE — Hanoi, Vietnam
**Embedded System Engineer – Senior Research Engineer** · Sep 2020 – July 2022

- Involved in design and implementation of the route-service module in Telematics products.

**Programming tasks**

- Developed middleware modules (Routing Service, HMI Service, SMS Service) for embedded systems.
- Implemented interfaces and APIs to pass requests and retrieve data asynchronously via Android Binders.
- Coded in compliance with AUTOSAR platform requirements.

**Research tasks**

- Researched and utilized the Telux SDK and Qualcomm IPA driver to support routing service (layer 3) and network connection.
- Diagnosed issues and bugs by investigating QXDM logs, proprietary logs, and interworking between various modules.

### Vinsmart — Hanoi, Vietnam
**QA Engineer** · Sep 2019 – Sep 2020

- Involved in quality assurance for Layer 2 operation. Tasks included designing and running test cases, debugging issues, and communicating with 3rd-party vendors to address them.
- Improved communication skills, team training, and technical writing.

**Programming tasks**

- Developed a DCI decoding tool and a TBS calculation tool with Java and Python to support testing tasks. Wrote C code to simulate PUCCH resources used during common procedures.

**Team training tasks**

- Presented 3GPP specifications to teammates on topics such as DL-CCH, UL-CCH, DMRS, HARQ, MCS, and TBS determination.


## Hobbies and Other Activities

- Writing technical blogs at [Technical Blogs – My Sky](https://freewindcode.com/blog/)

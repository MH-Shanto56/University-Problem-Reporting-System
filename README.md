# University Problem Reporting System (UPRS)
## Consolidated Project Analysis, Requirements and Development Blueprint

**Course:** CSE 302 — Object Oriented Programming II Lab: Visual and Web Programming Lab  
**Institution:** University of Asia Pacific (UAP), Department of CSE  
**Project:** University Problem Reporting System (UPRS)  
**Document type:** Analysis and implementation planning reference — **not** a statement that features have already been implemented  
**Based on:** 3 uploaded course/project documents  
**Analysis date:** 21 October 2026

---

## 1. Source Documents and What Each Contributes

| Source | Relevant content | How it is used here |
|---|---|---|
| **CSE-302-Project-Guidelines-1 (1).pdf** | Submission format, minimum features, individual contribution criteria, documentation sections, CEP rules, K/P/A definitions | **Authoritative project-submission requirements** |
| **UPRS.pptx.pptx** | UPRS proposal, problem statement, planned features, unique features, diagram, team names, initial CEP argument | **The team's planned project scope**, not implementation evidence |
| **CSE-302-Course-outline-Spring-2026.pdf** | Django/MVT learning objectives, CLO/PLO/K/P/A alignment, lab topics and evaluation distribution | **Tech-stack and academic alignment** |

**Important source locations:**
- Project Guidelines: p. 3 (full/zero marks and submission rules); pp. 4–5 (report format); pp. 7–10 (CEP method/example); pp. 13–16 (K/P/A definitions and CLO mapping).
- UPRS presentation: slides 2–6 (proposal and features), **slide 8 (existing class/ER-style diagram)**, slides 9–11 (K, A, P justifications).
- Course Outline: pp. 1–3 (objectives, CLO mapping), p. 4 (weekly topics), pp. 5–6 (assessment and grading).

### How to read this file

- **[REQUIRED]** = explicitly demanded by guideline/course outline.
- **[PROPOSED]** = described in your slide deck, but completion not verified.
- **[RECOMMENDED]** = suggested design or engineering improvement.
- **[VERIFY]** = confirm with instructor, team or actual GitHub project.

---

## 2. Executive Assessment

UPRS is a practical, real-world, Django-based reporting platform. Students submit campus issues and evidence, the system routes reports to relevant departments, staff handle problems, and students track status and provide feedback. Advanced proposed capabilities include similar-report detection, community support, priority suggestions and overdue monitoring.

**Feasibility assessment:** Good fit for CSE 302, provided the team builds and understands the code and scopes the smart features realistically. The proposal addresses a plausible Complex Engineering Problem (CEP), but final CEP claims should be backed by the implemented workflows and mapped to the actual course CLOs.

**What already appears structurally sufficient in the proposal:**
- **5 conceptual Django apps** (minimum 3).
- **14 visible model/class boxes** on slide 8 (minimum 7).
- **Multiple FK relationships** shown in the diagram (minimum 2).
- A role-based workflow and several potential CRUD entities.

**What is not established by the proposal alone:** functioning CRUD, working uploads and file deletion, secure authentication, routing rules, duplicate detection quality, git commit counts, code-line contributions, tests or deployment. These must be proved by the running implementation.

### Priority fixes

1. Define who can see, edit, assign, resolve and delete each report.
2. Correct ambiguities in department/user relationships and model field design.
3. Specify **two demonstrably complete CRUD workflows** and **media CRUD**.
4. Implement a simple, testable duplicate-detection method before adding complex NLP/ML.
5. Make priority, status and overdue rules deterministic and explainable.
6. Correct proposal/report formatting issues and use only permitted CLO–K/P/A mappings.
7. Track each person's required non-comment LOC, meaningful commits and ability to explain the code.

---

## 3. Official CSE 302 Requirements

### 3.1 Team-level [REQUIRED]

| Criterion | Official minimum or instruction | UPRS plan | Verification needed |
|---|---|---|---|
| Distinct Django apps | **At least 3 apps** | 5 shown conceptually | Confirm 3+ real Django apps in repository |
| Classes/models | **7+ classes across 3 different apps** | 14 class/model boxes | Verify Django model classes actually exist |
| Foreign keys | FK usage required; summary-table example indicates **minimum 2** | Many drawn | Confirm actual FK declarations, relations and working data |
| Media | **Media CRUD**; summary-table example indicates **2 uses/classes** | `Attachment` model drawn | Add/prove another appropriate media field or confirm teacher's interpretation; show media CRUD |
| Full CRUD | **At least 2 fully functioning CRUD operations/workflows** | Several candidates | Demonstrate create, list/detail, edit, delete for two entities |
| CEP | Well-documented justification | K/P/A argument drafted | Add precise evidence and CLO/PLO mapping |
| Design | Good design aesthetics | No final UI evidence in proposal | Build polished, responsive interface |

**Interpretation note:** The guideline describes media use generally and its project summary table shows `Use of Media: Required = 2`. To be safe, implement and document media handling in **at least two models/contexts**, not merely one uploaded image field.

### 3.2 Individual-level [REQUIRED]

Each team member must have:
- **500 or more lines of authored code excluding comments**.
- **8 or more meaningful Git commits**.
- Attendance at the individual final presentation/demo; absence is stated to lead to **0 presentation mark**.
- Enough understanding of their own code and the overall implementation to answer viva questions.

**For four members:** minimum targets are **2,000 non-comment lines combined** and **32 meaningful commits combined**, but satisfying combined totals does **not** substitute for each person's own minimum.

**Academic-integrity warning:** The guideline explicitly warns that copied projects or projects mostly/fully made using AI can receive **zero marks**. It states that code understanding may be checked through **3–6 questions**, with deductions for incorrect answers and potentially zero for failure to answer all. Use this document for planning; the team should implement, review, test and be able to explain its own work.

### 3.3 Report/submission [REQUIRED]

- Final documentation must be **15 pages or fewer**.
- **No raw source code** in the submitted report.
- Introduction is limited to **100 words**.
- Include an **image of the class diagram**, with a short explanation of the classes and foreign keys.
- Describe app structure, setup steps, dependencies and `requirements.txt`.
- Supply a **public GitHub repository URL** and screenshots of member contribution evidence.
- Provide a contribution table: member name, registration ID, GitHub username, commits, lines added and lines deleted.
- Provide a project summary comparing **required vs. actually implemented** counts.
- Add CEP justification **table + statement + K/P/A sources**, and key-feature screenshots with explanations.
- Submit the report **as PDF** before the lab demonstration and hand over any requested printed copy.

**[VERIFY — outdated due date]** The supplied guideline prints **06/06/26** as a printed-copy deadline. That date is in the past relative to this analysis (October 2026). Confirm the current batch's deadline directly with the instructor; do not present the old date as an upcoming one.

### 3.4 Assessment context

Course Outline p. 6: **Lab Performance 20%, Lab Test 20%, Project 60%**. The course evaluates implementation quality, practical Django skills, documentation and communication; merely submitting a polished proposal cannot substitute for a running project.

---

## 4. Original UPRS Problem Definition

### 4.1 [PROPOSED] Problem statement

Campus problems (e.g., broken facilities, cleanliness or safety concerns) are often reported through separate channels; students may not know which office is responsible, cannot reliably monitor progress, and may submit the same issue repeatedly. Departments have limited visibility into priority, responsibility, status and student confirmation.

**Slide correction:** The proposal contains the line **“Hard to connect finders with owners”** (slide 3). This appears inconsistent with campus *problem reporting*, and should be rewritten to **“Hard to connect submitted reports with the responsible department or staff.”**

### 4.2 [PROPOSED] Objectives

1. Centralize incident reporting with location, category, text and photo evidence.
2. Route reports to the responsible department.
3. Track issues through clear status changes.
4. Allow department staff to manage assignments and responses.
5. Notify users and support two-way comments.
6. Capture feedback/confirmation after resolution.
7. Reduce duplicates, identify widespread issues and surface overdue reports.

### 4.3 Stakeholders

| Actor | Main needs | Key constraints |
|---|---|---|
| Student | Easy reporting, tracking, notifications, privacy, feedback | Access only authorized information |
| Department admin | Queue management, categorization, staff assignment, priority decisions | Department-scoped access, auditability |
| Staff | Assigned tasks, status updates, comments | Can change only authorized reports |
| System admin | Accounts, departments, categories, oversight | Least privilege, security, audit logs |
| University management (optional) | Aggregate visibility and trends | Avoid unnecessary exposure of personal data |

---

## 5. Proposed Features: Scope and Acceptance Criteria

| Feature | Source status | Minimum demonstrable behavior | Phase |
|---|---|---|---|
| Authentication and roles | [PROPOSED] | Login/logout and proper permission checks | MVP |
| Problem submission | [PROPOSED] | Student creates report with category, location, description | MVP |
| Evidence upload | [PROPOSED] | Upload, view, update/remove attachments with validation | MVP |
| Automatic department routing | [PROPOSED] | Category determines default responsible department | MVP |
| Status tracking | [PROPOSED] | Submitted → In Progress → Resolved → Closed | MVP |
| Staff assignment | [PROPOSED] | Authorized department admin assigns relevant staff | MVP |
| Comments and notifications | [PROPOSED] | Authorized parties communicate and see updates | MVP/Phase 2 |
| Priority management | [PROPOSED] | Low / Medium / High / Urgent with visible rules | MVP/Phase 2 |
| Feedback/verification | [PROPOSED] | Reporter rates/comments on a resolved report | Phase 2 |
| Similar-report detection | [PROPOSED UNIQUE] | Show potential matches before duplicate submission | Phase 2 |
| Community support | [PROPOSED UNIQUE] | One support/upvote per student per report | Phase 2 |
| Smart priority suggestion | [PROPOSED UNIQUE] | Suggest priority using understandable scoring | Phase 3 |
| Overdue monitoring | [PROPOSED UNIQUE] | Flag unresolved reports past a documented deadline | Phase 3 |

**Recommended scope:** Build the entire MVP with tests before attempting all “smart” features. A reliable category/location-based similarity check and explainable priority scoring are valid course-project engineering solutions; machine learning is **not required by the supplied documents**.

### 5.1 Suggested functional acceptance tests

- A student can create a report, see it in “My Reports”, and open its detail page.
- An unauthenticated visitor cannot access private reports.
- A student cannot edit someone else's report by changing the URL or request payload.
- A report's responsible department matches its category by default; an authorized admin can handle exceptional routing.
- Only permitted staff/admin can assign or update a report.
- Every legitimate status change creates a `StatusHistory` record.
- Students can view appropriate updates and mark notifications read.
- An attachment can be uploaded, shown and removed by an authorized user.
- A student cannot support the same report twice.
- An issue cannot be silently closed by an unrelated user.

---

## 6. Analysis of the Existing Class Diagram (UPRS slide 8)

### 6.1 Exact structural inventory (as illustrated)

The slide groups **14 model/class boxes into 5 labeled app areas**:

| App area in diagram | Models shown | Count |
|---|---|---:|
| Student & Authentication App | `User`, `Student`, `Staff`, `Admin` | 4 |
| Department App | `Department`, `Category` | 2 |
| Problem App | `ProblemReport`, `Location`, `Attachment`, `StatusHistory`, `Comment`, `ProblemSupport` | 6 |
| Feedback App | `Feedback` | 1 |
| Notification System App | `Notification` | 1 |
| **Total** | | **14** |

**Caution:** The diagram looks more like an **ER/data model diagram** (fields, PKs and FKs) than a complete UML class diagram (which often includes methods, multiplicities and explicit association notation). Because the guideline specifically requests a class diagram, consider adding relationship cardinalities and a short model responsibility description. It can still be presented as the database-backed model/class architecture if acceptable to your teacher.

### 6.2 Inventory of primary relationships from the diagram

- `Student.user_id → User`
- `Staff.user_id → User`
- `Staff.department_id → Department`
- `Admin.user_id → User`
- `Category.department_id → Department`
- `ProblemReport.student_id → Student`
- `ProblemReport.category_id → Category`
- `ProblemReport.location_id → Location`
- `ProblemReport.department_id → Department`
- `ProblemReport.assigned_staff_id → Staff`
- `Attachment.report_id → ProblemReport`
- `StatusHistory.report_id → ProblemReport`
- `StatusHistory.changed_by → User`
- `Comment.report_id → ProblemReport`
- `Comment.user_id → User`
- `ProblemSupport.report_id → ProblemReport`
- `ProblemSupport.student_id → Student`
- `Feedback.report_id → ProblemReport`
- `Feedback.student_id → Student`
- `Notification.user_id → User`

This is an analysis of the **drawn** relationships, not a claim that the ORM currently contains them.

### 6.3 Problems and improvements to resolve

| Existing design concern | Why it matters | [RECOMMENDED] correction |
|---|---|---|
| `User.password: string` appears on the slide | Could imply unsafe plain-text password handling | **Use Django's built-in authentication/password hashing**; never store plain-text passwords |
| `Staff.department_id` FK plus `Staff.department` string | Duplicates a source of truth | Keep the FK; read department name through the relation |
| `Admin.department` is a string | Department-admin scope becomes ambiguous | Link department admins to a `Department` FK where appropriate; separate superuser privileges |
| Student's `department` field is free text | Can become inconsistent with official department records | Use academic department FK **if needed**; distinguish student's academic unit from the *responsible service department* |
| `ProblemReport.category_id` and `department_id` coexist | Could be inconsistent | Auto-fill assigned department from category; permit audited authorized override |
| `ProblemReport.priority` / `status` stored as strings | Risk of typos and invalid values | Define fixed choices and validated transitions |
| No explicit `severity` field | Difficult to calculate proposed smart priority | Add structured severity **if scoring will use it** |
| No explicit expected resolution deadline | Cannot reliably detect overdue reports | Add `due_at` or derive an SLA from category/priority; optional initial phase |
| `ProblemSupport` has no uniqueness rule shown | Duplicate support inflates counts | Unique constraint on `(report, student)` |
| `Feedback` has no submission rule shown | Duplicate/unauthorized feedback | Reporter-only permission; normally one feedback per report |
| Media fields shown only on `Attachment` | Guideline's summary table expects 2 media uses | Add meaningful media to a second model, e.g., `Category.icon` or `Student.profile_photo` |
| Report deletion and audit not defined | Historical records can be lost | Define who may delete; protect existing referenced data and log key actions |
| `StatusHistory.changed_by` type/ownership | No trustworthy audit without current user | Set server-side from authenticated user; never trust user-provided actor IDs |

### 6.4 Practical, safer model blueprint

Retain the **14 original conceptual models**, refine attributes and constraints:

| Model | Key data / relationship | Important policy |
|---|---|---|
| `User` | Django authentication account + role/group | Hashed passwords, validated email, authorization |
| `Student` | One-to-one `User`, registration/student ID, optional media | Student ID unique |
| `Staff` | One-to-one `User`, FK to service `Department` | Department-scoped actions |
| `Admin` | One-to-one `User`, optional FK to `Department` | Distinguish departmental from system admin |
| `Department` | Name, description, active flag | Referential integrity; prevent unsafe deletion |
| `Category` | Name, FK to responsible `Department`, optional `icon` media | Routed to designated department |
| `Location` | Campus, building, floor, room | Normalize input where possible |
| `ProblemReport` | FK Student/Category/Location/Department/Staff; title, description, status, priority, tracking number, timestamps | Owner permissions, validated transitions |
| `Attachment` | FK Report, file/image, upload time | File size/type checks, ownership checks |
| `StatusHistory` | FK Report, prior/new status, actor, timestamp | Append-only audit history |
| `Comment` | FK Report, FK User, message, created time | Authorized visibility/editing |
| `ProblemSupport` | FK Report, FK Student, created time | Unique(report, student) |
| `Feedback` | FK Report, FK Student, rating/comment | Only eligible reporting student may submit |
| `Notification` | FK User, message, is_read, created time | Private per-user inbox |

Optional extra entities such as `PriorityHistory`, `Escalation`, `ReportDuplicateLink` and `AuditLog` should be introduced only when the feature and workload justify them. The minimum 14-model architecture already exceeds the rubric requirement.

---

## 7. Recommended Django Architecture

### 7.1 Five apps matching the proposal

| Django app | Proposed models | Responsibility |
|---|---|---|
| `accounts` | `Student`, `Staff`, `Admin`; Django `User` | Authentication, profiles, roles |
| `departments` | `Department`, `Category` | Routing categories and service units |
| `reports` | `ProblemReport`, `Location`, `Attachment`, `StatusHistory`, `Comment`, `ProblemSupport` | Core reporting lifecycle |
| `feedback` | `Feedback` | Reporter ratings and resolution verification |
| `notifications` | `Notification` | In-app updates and read/unread state |

Use **Django MVT**, HTML/CSS/JavaScript and Bootstrap or equivalent responsive styling. Django ORM relationships, views, forms, templates, routing, authentication and media handling are all aligned with the course outline. **SQLite** is adequate for local prototyping; PostgreSQL is an optional later deployment choice, not an explicit course requirement.

### 7.2 Simple architecture flow

**Browser UI → Django URL/view → authentication and permission checks → validation/form → domain logic (routing/status/priority) → Django ORM/database → template/notification/audit.**

Keep business decisions (such as assigning departments and deciding status transitions) in readable, testable application logic rather than scattering duplicated rules across HTML templates and unrelated views.

### 7.3 Role-permission matrix (recommended baseline)

| Action | Student | Assigned staff | Department admin | System admin |
|---|---:|---:|---:|---:|
| Submit own report | Yes | No* | No* | Yes* |
| View own report | Yes | — | — | Yes |
| View department-assigned report | Own only | Assigned | Own department | Yes |
| Update report description | Own, while permitted | No | Limited/controlled | Yes |
| Assign/transfer staff | No | No | Own department | Yes |
| Change workflow status | No (except confirmation, if designed) | Assigned | Own department | Yes |
| Manage department/category records | No | No | Authorized scope | Yes |
| Upload attachment | Own report | Authorized scope | Authorized scope | Yes |
| View own notifications | Yes | Yes | Yes | Yes |
| Submit satisfaction feedback | Eligible reporter | No | No | No |

`*` Depends on whether users may hold multiple roles. Explicitly choose either **single-role accounts** or **Django Group/Permission-based multiple roles** to avoid contradictions. “Own only” and “own department” checks must run **server-side**, not merely hide frontend buttons.

---

## 8. Required CRUD Demonstration Plan

### CRUD workflow A — Category management [RECOMMENDED]

- **Create:** department/system admin adds category, description, responsible department, optional icon.
- **Read:** list and detail pages show categories and department.
- **Update:** edit name, routing department and icon.
- **Delete:** permitted when not referenced, or use a clearly explained restricted deletion policy.

### CRUD workflow B — Location management [RECOMMENDED]

- **Create:** admin adds campus/building/floor/room.
- **Read:** location listing/detail.
- **Update:** edit location information.
- **Delete:** prohibit destructive deletion of locations already used by reports, or handle through a documented alternative demonstrating actual delete functionality where valid.

Both workflows are comparatively easy to demo as **complete CRUD**. Also deliver report creation, owner-facing read/update, and a well-defined deletion/archiving policy; do not assume “archive” alone automatically qualifies as Delete for the course rubric.

### Media CRUD [RECOMMENDED]

1. `Attachment.file` for report evidence.
2. `Category.icon` **or** `Student.profile_photo` for a second appropriate media use.
3. Demonstrate upload/create, preview/read, replace/update and removal/delete where authorized.
4. Validate image/file extensions, MIME assumptions, file size and ownership. Do not make uploaded private evidence publicly guessable by URL without access controls.

> **Evidence:** Final PDF should include screenshots of both CRUD workflows and media actions, plus a summary table with the **actual implemented** numbers.

---

## 9. Functional Workflow and Business Rules

### 9.1 Report submission

1. User signs in as student.
2. Student selects category and location and enters title/description.
3. Student attaches optional evidence.
4. Server validates inputs and creates a unique tracking number.
5. System assigns default department using category-to-department relation.
6. Save report as `Submitted`, create initial history, notify the appropriate queue.
7. Student can see report ID, current status and timestamp.

### 9.2 Status workflow

**Initial proposed sequence:** `Submitted → In Progress → Resolved → Closed`.

| Transition | Suggested authorized actor | Conditions |
|---|---|---|
| Submit → In Progress | Assigned staff or department admin | Assignment and permission verified |
| In Progress → Resolved | Staff or department admin | Evidence/remarks of work completed |
| Resolved → Closed | Reporter confirmation or authorized admin | Feedback policy respected |

**[RECOMMENDED] Optional states:** `Rejected` (with reason), `Reopened` (if reported fix fails). These do **not** appear in the four-state proposal and should be approved as extensions. Every transition should set `updated_at` and add a `StatusHistory` row.

### 9.3 Automated routing

Default: `report.category.department` → `report.department`.  
Reject inconsistent manual changes unless authorized; do not automatically assign a staff member in another department. If a category's default department changes later, decide explicitly whether existing reports keep their current assigned department (recommended for historical integrity).

### 9.4 Similarity/duplicate detection — realistic MVP

**[RECOMMENDED] Rule-based version, before submission:**
- Compare active reports with matching or nearby `Location` and same `Category`.
- Normalize text (lowercase, remove trivial punctuation/stop words) and compare words in title and description.
- Show top likely matches with tracking IDs and status.
- Let student **support an existing report** or continue submitting a new report if it is genuinely different.
- Do not automatically merge reports without evidence and authorization.

**Limitations:** Similar wording can refer to unrelated incidents, and different wording can describe one issue. Show results as “possibly similar,” not a guaranteed duplicate. TF-IDF or embeddings can be a later enhancement **only if the team understands and can explain the approach**.

### 9.5 Community support

One student can support one report once. Use database uniqueness and server-side authorization. A count of supports is an **affected-student signal**, not proof that every supporter has independently verified the incident.

### 9.6 Explainable priority suggestion

Priority options from proposal: `Low`, `Medium`, `High`, `Urgent`.

**Suggested optional design:** compute a recommendation from **reported severity + number of unique supporters + report age + category-specific urgency**, then show the underlying reasons. Allow authorized staff to change final priority with a recorded explanation. Avoid silently escalating every popular complaint to `Urgent`; safety-critical issues require human judgment.

### 9.7 Overdue monitoring

**Prerequisite:** define a target resolution time, e.g., category-level SLA or explicit `due_at` field. A report is overdue only if **not in a finished state** and past its defined due date. Display it on the department queue and optionally create notifications. Deadline values must come from administrator-defined policy; **no actual university SLA is provided in the source slides**.

---

## 10. Nonfunctional Requirements

| Area | Recommended measurable check |
|---|---|
| Security | Django password hashing, authenticated routes, object-level permission checks, CSRF safeguards |
| Input validation | Required fields, max lengths, restricted status/priority values, sensible form errors |
| Media protection | Validate allowed type/size, safe filenames/paths, authorized file access |
| Consistency | Transactions for report+history or assignments+notifications when necessary |
| Integrity | Database FKs, uniqueness for tracking number and support records |
| Accessibility | Legible contrast, keyboard-accessible form controls, accessible validation messages |
| Responsive design | Test student dashboard and report submission on mobile and desktop |
| Performance | Pagination and indexes for common filters (status, department, created date) |
| Maintainability | Clear separation of Django apps, descriptive names, reproducible setup |
| Auditability | Status transitions and sensitive assignment changes show the actor/time |
| Privacy | Avoid exposing unnecessary student identifiers and personal attachments publicly |

**Recommended search/filters:** student can search own tracking numbers; department dashboard can filter by status, priority, location, assigned staff and date. Search/filter functionality is part of the CSE 302 weekly content.

---

## 11. CEP: Academic Alignment and Revised Justification

### 11.1 Minimum CEP test from the guideline

A project qualifies as a **Complex Engineering Problem (CEP)** only when its supported argument contains:

1. **P1 (mandatory)** — requires in-depth engineering knowledge.
2. **At least one** further attribute from **P2–P7**.
3. **At least one** applicable activity from **A1–A5**.

The guideline advises **3–5 Knowledge (K) attributes**, roughly **10–14 total K/P/A selections at most**, and **only mappings present in the course outline**. Do not select every possible attribute just to increase the count.

### 11.2 K/P/A mappings actually available in the CSE 302 outline

| CLO | PLO | Allowed K | Allowed P | Allowed A |
|---|---|---|---|---|
| CLO1 | PLO-a | K3 | P1 | A2 |
| CLO2 | PLO-b | K5 | P2 | A2 |
| CLO3 | PLO-c | K4, K5 | P3 | A2 |
| CLO4 | PLO-e | K6 | P7 | A4 |
| CLO5 | PLO-i | K6 | P1 | A5 |
| CLO6 | PLO-j | K7 | P3 | A2 |

**Important:** Some examples in the generic guideline mention other K/P/A types, but the actual course outline above limits what the team should map for **this** course. The proposal's K3, K4, K5, K6, K7; P1, P2, P3, P7; and A2, A4 are all found in that outline.

### 11.3 Project-specific CEP justification table (11 selected attributes)

| Type | Attribute | Specific UPRS justification | Correct matching CLO(s) / PLO(s) |
|---|---|---|---|
| K | **K3** — Engineering fundamentals | Applies OOP, web architecture, request/response logic, data integrity and schema relationships to route and track campus reports | CLO1 / PLO-a |
| K | **K4** — Specialist engineering knowledge | Requires Django MVT, authentication, ORM relationships and permission-aware views | CLO3 / PLO-c |
| K | **K5** — Knowledge supporting design | Converts differing student/staff/admin needs into data models, report states and workflow rules | CLO2–CLO3 / PLO-b, PLO-c |
| K | **K6** — Engineering practice | Uses Django, Git/GitHub, deployment/setup, media handling and repeatable testing | CLO4–CLO5 / PLO-e, PLO-i |
| K | **K7** — Engineering in society | Considers student privacy, accountability, misuse prevention and institutional transparency | CLO6 / PLO-j |
| P | **P1** — In-depth knowledge (mandatory) | Multiple interrelated technical layers—auth, access control, models, media, routing, workflows and audit—need integrated engineering reasoning | CLO1, CLO5 / PLO-a, PLO-i |
| P | **P2** — Conflicting requirements | Students seek simple and transparent reporting while departments need verification, privacy and restricted access | CLO2 / PLO-b |
| P | **P3** — No obvious solution | Duplicate identification, department routing, priority and escalation policies require design trade-offs and analysis | CLO3, CLO6 / PLO-c, PLO-j |
| P | **P7** — Interdependent components | User roles, categories, reports, departments, assigned staff, history, support, feedback and notifications affect one another | CLO4 / PLO-e |
| A | **A2** — Resolving conflicting issues | Balances easy reporting vs. abuse prevention, open updates vs. private data and quick action vs. fair prioritization | CLO1–CLO3, CLO6 / PLO-a, PLO-b, PLO-c, PLO-j |
| A | **A4** — Significant consequences | Incorrect routing or leaked evidence can undermine campus safety, trust and the response process | CLO4 / PLO-e |

The table is a **proposed justification**. During implementation, each row should be backed by real examples from your architecture, code behavior, screenshots, tests and design decisions.

### 11.4 Ready-to-adapt CEP justification statement

> The University Problem Reporting System addresses a Complex Engineering Problem because its implementation requires integrated knowledge of software design, Django MVT architecture, authentication, database relationships and secure application development (P1). It further involves conflicting stakeholder requirements between transparency, privacy and ease of access (P2); design decisions without a single obvious solution for report routing, prioritization and duplicate handling (P3); and interdependent system components such as reporting, departmental assignments, feedback and notifications (P7). The project requires resolving technical and organizational trade-offs (A2) and considers the significant consequences of incorrect routing or mishandling sensitive reports (A4). The solution is supported by relevant K3–K7 knowledge and the mapped CLOs of CSE 302.

**Editing rule:** If duplicate detection, overdue tracking or other elements are not implemented, describe them as planned and rely on **implemented** parts for final CEP evidence.

---

## 12. CLO Evidence Plan

| Course outcome | What the team should present |
|---|---|
| CLO1 — OOP and web basics | Explain classes, inheritance/relationships, templates, HTML/CSS and backend flow |
| CLO2 — Requirement analysis | User roles, problem statement, competing needs, functional/nonfunctional requirements |
| CLO3 — Design | Class/ER diagram, 5-app architecture, data relationships, key design decisions |
| CLO4 — Secure Django implementation | Running authenticated app, CRUD, routing, media, responsive pages, working permissions |
| CLO5 — Collaboration | GitHub commits, merged work, contribution table, per-member ownership and teamwork |
| CLO6 — Documentation and oral presentation | Accurate <=15-page report, screenshots, CEP table, explanation and confident viva |

---

## 13. Team and Contribution Plan

### 13.1 Members listed on proposal slide 2

| Team member | Registration ID | Suggested primary ownership — **not confirmed assignment** |
|---|---|---|
| Mehedi Hasan Shanto | 24101102 | Accounts, authentication and role permissions |
| Shahariar Arabin | 24101092 | Reports, locations, attachments, tracking/history |
| Nur Nahar | 24101107 | Departments/categories, automatic routing, admin dashboard |
| Jannat Nahar Rimi | 24101108 | Feedback, notifications, support/duplicate UI and UX |

These are **suggestions only**. Agree on actual assignments within the team and distribute sufficient implementation work to meet **each person's** minimum LOC/commits. Shared work may include frontend integration, testing and documentation, but contributions must be truthful and attributable in Git.

### 13.2 Suggested development phases

| Phase | Objective | Proof of completion |
|---|---|---|
| **1. Foundation** | Agree requirements, Git workflow, Django project, models and migrations | Repo, shared setup, schema diagram, login working |
| **2. Core CRUD** | Category/location CRUD; report create/list/detail/update, evidence | Two complete CRUD demos, uploads, validated forms |
| **3. Workflow** | Routing, roles, staff assignment, status history, dashboard | Multi-role end-to-end demo and permission tests |
| **4. Communication** | Comments, notifications, feedback, support counts | Real records and UI screenshots |
| **5. Smart features** | Similarity candidates, explainable priority, overdue tracking | Tests showing correct and incorrect scenarios |
| **6. Quality and submission** | Security checks, polish, documentation, Git verification, mock viva | Ready running demo and accurate <=15-page PDF |

**Project hygiene:** Keep commits specific (“add department-based routing validation”, “test unauthorized report access”), avoid meaningless repeated commits, and regularly review merge conflicts and migrations. Do not inflate LOC with boilerplate or duplicate code.

---

## 14. Testing Checklist

### Core behavior

- [ ] Registration/login/logout work as designed.
- [ ] User roles and department scope are enforced server-side.
- [ ] Department and Category relationships function.
- [ ] At least two full CRUD workflows are demo-ready.
- [ ] Student can create and view their own report with a tracking number.
- [ ] Report is auto-routed to the expected department.
- [ ] Appropriate staff can be assigned.
- [ ] Status updates persist and write an audit/history entry.
- [ ] Evidence upload, retrieval, replacement and removal are tested.
- [ ] At least two model/context media uses are documented (if using the conservative rubric interpretation).
- [ ] Comments and notifications respect user access.
- [ ] Feedback can be submitted only by an eligible student.
- [ ] Report-support duplicates are blocked.

### Security and failure cases

- [ ] Unauthorized users get a refusal (not another person's data).
- [ ] Forged student, staff or department IDs cannot bypass permission checks.
- [ ] Invalid file type/oversized upload is rejected.
- [ ] Invalid status changes are rejected.
- [ ] Missing required form data shows understandable errors.
- [ ] Deletion of referenced category/location is safely handled.
- [ ] Notification access is restricted to its owner.
- [ ] Similar-report detection allows legitimate distinct reports.
- [ ] Priority/overdue rules are tested if implemented.
- [ ] Mobile layout and keyboard/form usability are checked.

### Evidence and submission

- [ ] All team members meet 500+ non-comment LOC **individually**.
- [ ] All team members have 8+ meaningful commits **individually**.
- [ ] Public GitHub repo and contribution screenshots available.
- [ ] Implemented model/app/FK/media/CRUD counts checked from repo.
- [ ] Class diagram accurately represents implemented models.
- [ ] CEP uses only permitted K/P/A–CLO mappings.
- [ ] Report is <=15 pages, introduction <=100 words and has no raw source code.
- [ ] Current submission deadline confirmed with instructor.
- [ ] Each presenter can explain models, FKs, permissions, status transitions and their own code.

---

## 15. Suggested Final PDF Report Structure (Within 15 Pages)

This is a **page-budget suggestion**, not an instruction to misrepresent unfinished work.

| Section | Target pages | Content |
|---|---:|---|
| Cover | 1 | University, course, project, instructor, members and IDs |
| Introduction | 0.5 | <=100 words; problem, motivation and purpose |
| Class diagram + explanation | 2 | Actual diagram as image; models, relationships and FKs |
| Project structure | 1 | Number of actual Django apps and responsibilities |
| Installation/setup | 1 | Environment, dependencies, `requirements.txt`, configuration |
| Key features/screenshots | 3 | Report submission, CRUD, routing, role dashboards, media, optional smart features |
| Project summary table | 1 | Minimum requirements vs **actual** completed counts |
| GitHub contributions | 1.5 | Public link, screenshots, member table |
| CEP justification | 2 | Evidence-based mapped table and statement |
| Testing/conclusion | 1 | Demonstration checks, limitations and outcome |
| **Total suggested** | **14** | Leaves ~1 page for layout adjustments |

Follow the **official template's required sections** even if the internal ordering or page distribution changes. Do not insert raw implementation code into this submission PDF.

### Project summary table — fill only after implementation

| Component | Required | Actual completed | Proof / notes |
|---|---:|---|---|
| Django apps | 3 | **TBD** | Names of existing Django apps |
| Classes/models | 7 | **TBD** | List actual Django model classes |
| Foreign keys | 2 | **TBD** | Show relationships and reasons |
| Media uses | 2 (summary table) | **TBD** | Name media-bearing models |
| Full CRUD workflows | 2 | **TBD** | Name entities and demonstrate all four operations |
| CEP evidence | Required | **TBD** | Justification with course mapping |

### Contribution table — fill using GitHub evidence

| SL | Full name | Registration ID | GitHub username | Meaningful commits | Lines added | Lines deleted | Non-comment LOC authored |
|---:|---|---|---|---:|---:|---:|---:|
| 1 | Mehedi Hasan Shanto | 24101102 | TBD | TBD | TBD | TBD | TBD |
| 2 | Shahariar Arabin | 24101092 | TBD | TBD | TBD | TBD | TBD |
| 3 | Nur Nahar | 24101107 | TBD | TBD | TBD | TBD | TBD |
| 4 | Jannat Nahar Rimi | 24101108 | TBD | TBD | TBD | TBD | TBD |

GitHub “lines added/deleted” statistics and a person's **non-comment lines of authored code** measure different things. Track both without treating them as interchangeable.

---

## 16. Presentation Slide Corrections

The current proposal is a useful starting point. Before final presentation/documentation:

1. Replace slide 3's unrelated **“finders with owners”** wording with responsible-department routing.
2. Make the distinction between **what you propose** and **what already works** visible.
3. Slide 8's diagram should match the actual ORM models and contain legible relationship/cardinality markings.
4. Clarify `Admin` vs department admin vs Django superuser; avoid duplicate department strings.
5. Slides 9 and 10 repeat the **same A2/A4 activity-justification table**; remove the duplicate.
6. Slides 10 and 11 use inconsistent/duplicated section numbering; renumber neatly.
7. Replace broad claims about “smart” prioritization and duplicate detection with the chosen algorithm, inputs, conditions and limits.
8. Add a concise **CLO/PLO column** to the CEP mapping instead of presenting unaligned generic K/P/A descriptions.
9. Include an actual UI demonstration or screenshots, not only feature descriptions.
10. Fix small wording issues and ensure a consistent, uncluttered theme.

---

## 17. Open Decisions the Team Must Confirm

| Decision | Recommended default |
|---|---|
| Are students allowed to report anonymously? | **No in MVP**; authenticated reports reduce misuse. If anonymous reporting is needed, separately design privacy and moderation. |
| Does an admin have one department or global authority? | Department admin is scoped; Django superuser/system admin is global. |
| Who can close a resolved report? | Reporter confirmation or documented department-admin override. |
| Can students delete reports? | Restrict to a clear early-stage rule or archive; explicitly meet rubric via two other full CRUD entities. |
| Does a change in category routing migrate old reports? | Keep old assigned department unless authorized action explicitly reassigns. |
| What is duplicate detection? | Start with category + location + text similarity on active reports. |
| What marks a report overdue? | University/admin-defined resolution deadline, not an invented SLA. |
| What constitutes valid feedback? | One submission from eligible reporter after resolution. |
| What second model should use media? | Category icon or Student profile photo; agree with team. |
| What are the actual due date and grading expectations? | Confirm with current course instructor. |
| What has already been coded? | Check real repository; this analysis is based on **proposal** not code. |

---

## 18. Final Recommendation / Next Action

**Recommended build order:**

**Authentication + 5-app structure → FKs and migrations → two complete CRUD modules → report submission and attachments → secure permissions/department routing → status/history → notifications/feedback → unique features → testing → Git evidence → final <=15-page PDF.**

**Minimum success condition:** A working, student-developed and defensible Django project that satisfies the teacher's measurable app/class/FK/media/CRUD, Git contribution, CEP and documentation requirements.

**Higher-quality success condition:** Beyond the minimum, the project has predictable workflows, strong per-object authorization, transparent reporting, reproducible setup, explainable priority/deduplication rules and a clean mobile-friendly interface.

**Main risk:** Building many attractive “smart” screens without implementing the minimum verified CRUD, media, secure role permissions and traceable per-member contributions. Prioritize **demonstrable functionality and code understanding** over feature count.

---

## References (Uploaded Documents)

1. *CSE-302-Project-Guidelines-1 (1).pdf*, University of Asia Pacific, project template and CEP guidance (16 PDF pages).
2. *UPRS.pptx.pptx*, University Problem Reporting System: Project Proposal & Development Plan (13 slides).
3. *CSE-302-Course-outline-Spring-2026.pdf*, CSE 302 Spring 2026 course outline, University of Asia Pacific (6 PDF pages).

**Prepared as a consolidated planning/analysis reference.** It is **not** a replacement for the required official PDF submission and does **not** verify repository implementation or contribution statistics.

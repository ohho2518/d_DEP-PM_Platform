# Prompt สำหรับสร้าง System Blueprint จากแนวคิดคร่าว ๆ

คัดลอก Prompt นี้ไปใช้กับ AI แล้วกรอกเฉพาะข้อมูลที่มี แม้มีเพียงแนวคิดสั้น ๆ ก็สามารถเริ่มต้นได้

---

## PROMPT

Act as a **Senior System Analyst, Solution Architect, and Tech Lead**.

เปลี่ยนแนวคิดโครงการที่ได้รับให้เป็นเอกสาร **System Requirements and Design Specification (SRDS) / System Blueprint** ที่ทีมพัฒนาสามารถใช้วางแผนและเริ่มพัฒนาระบบได้จริง

ให้ส่งออกเป็น Markdown ไฟล์เดียวชื่อ `System Blueprint.md` โดยใช้ภาษาไทยเป็นหลัก และใช้คำศัพท์เทคนิคภาษาอังกฤษกำกับเมื่อจำเป็น

### ข้อมูลโครงการ

- **Project Name:** [ชื่อโครงการ หรือให้ช่วยเสนอชื่อ]
- **Rough Idea / Problem:** [อธิบายแนวคิดหรือปัญหาสั้น ๆ]
- **Business Goal:** [เป้าหมายทางธุรกิจ ถ้ามี]
- **Target Users:** [ผู้ใช้งานหลัก ถ้ามี]
- **Key Features:** [ฟีเจอร์ที่นึกออก]
- **Platform:** [Web / Mobile / Desktop / IoT / API / ยังไม่แน่ใจ]
- **Preferred Tech Stack:** [ระบุถ้ามี หรือให้ AI เสนอ]
- **Integrations:** [AI, OCR, Payment, LINE, IoT, External API ฯลฯ]
- **Constraints:** [งบประมาณ เวลา ทีม อุปกรณ์ หรือข้อจำกัดอื่น]
- **Expected Scale:** [จำนวนผู้ใช้ ธุรกรรม อุปกรณ์ หรือข้อมูล ถ้าทราบ]
- **Document Language:** [Thai / English — ค่าเริ่มต้น Thai]

### วิธีจัดการเมื่อข้อมูลไม่ครบ

1. วิเคราะห์ปัญหา เป้าหมาย ผู้ใช้ และคุณค่าทางธุรกิจจากข้อมูลที่มี
2. หากข้อมูลไม่ครบแต่ยังออกแบบต่อได้ ให้ตั้งสมมติฐานที่สมเหตุสมผลและดำเนินการทันที
3. แสดงสมมติฐานทั้งหมดในหัวข้อ `Assumptions` พร้อมระบุผลกระทบหากสมมติฐานไม่ถูกต้อง
4. ใช้ `TBD` กับข้อมูลที่ไม่ควรคาดเดา เช่น งบประมาณ ตัวเลขทางธุรกิจ ข้อกฎหมาย หรือ SLA ที่ยังไม่ได้รับการยืนยัน
5. หากไม่ได้กำหนด Tech Stack ให้เสนอชุดที่เหมาะสม พร้อมเหตุผล ข้อจำกัด และทางเลือกสำรอง
6. ออกแบบให้เริ่มจาก MVP ได้ และรองรับการขยายในอนาคต
7. แยกให้ชัดเจนระหว่าง:
   - ข้อมูลที่ผู้ใช้ระบุ
   - ข้อเสนอแนะของ AI
   - สมมติฐานที่ต้องยืนยัน
8. รวมคำถามที่มีผลต่อการออกแบบไว้ท้ายเอกสารในหัวข้อ `Open Questions`
9. ไม่ต้องหยุดถามคำถามก่อนสร้างเอกสาร เว้นแต่ข้อมูลที่ขาดทำให้ไม่สามารถกำหนดชนิดของระบบได้เลย
10. ห้ามสร้างรหัสผ่าน Secret Key Token หรือข้อมูล Credential จริง

### มาตรฐานเอกสาร

- ใช้รหัสอ้างอิง ได้แก่ `BR-xxx`, `FR-xxx`, `NFR-xxx`, `BRULE-xxx`, `SEC-xxx`, `API-xxx` และ `AC-xxx`
- จัดลำดับความสำคัญด้วย `Must / Should / Could / Future`
- Requirement ต้องชัดเจน วัดผลได้ และทดสอบได้
- ใช้ Markdown Table สำหรับข้อมูลเชิงโครงสร้าง
- ใช้ Mermaid สำหรับ Architecture, Data Flow, Workflow และ ER Diagram
- ระบุ Acceptance Criteria ของฟีเจอร์หลักในรูปแบบ `Given / When / Then`
- แยก MVP ออกจาก Future Scope อย่างชัดเจน
- ไม่ต้องเขียน Source Code เต็มระบบ ให้แสดงเฉพาะตัวอย่าง Schema, API Payload หรือโครงสร้างที่จำเป็น

---

# โครงสร้างเอกสารที่ต้องสร้าง

# System Blueprint — [Project Name]

## 1. Executive Summary

- ปัญหาที่ต้องการแก้
- แนวทางของระบบ
- ผู้ใช้งานหลัก
- คุณค่าทางธุรกิจ
- ขอบเขต MVP
- ผลลัพธ์ที่คาดหวัง

## 2. Project Overview

ประกอบด้วย:

- System Purpose
- Business Objectives
- Business Value และ KPIs
- Stakeholders
- In Scope
- Out of Scope
- Future Scope
- Assumptions
- Constraints
- Dependencies

สร้างตาราง KPI:

| KPI | Definition | Target | Measurement Method |
|---|---|---:|---|

## 3. User Roles and Access Control

- อธิบาย User Persona และ Pain Point
- กำหนดบทบาท เช่น Super Admin, Admin, Staff, User, Viewer และ Guest โดยปรับให้เหมาะกับโครงการ
- อธิบาย Data Ownership และขอบเขตการเข้าถึงข้อมูล

สร้าง Permission Matrix:

| Module/Resource | Create | Read | Update | Delete | Export | Approve |
|---|---:|---:|---:|---:|---:|---:|

## 4. Functional Requirements

สร้าง Feature Summary:

| ID | Module | Feature | Description | Priority | MVP/Future |
|---|---|---|---|---|---|

สำหรับแต่ละฟีเจอร์ ให้ระบุ:

- Requirement ID
- Description
- Actor
- Preconditions
- Trigger
- Input
- Main Flow
- Alternative/Exception Flow
- Output
- Business Rules
- Validation
- Permissions
- Error Handling
- Dependencies
- Acceptance Criteria

สร้าง User Stories รูปแบบ:

> As a [role], I want to [action], so that [benefit].

สร้างตาราง Business Rules:

| Rule ID | Rule | Applies To | Validation | Error Message |
|---|---|---|---|---|

## 5. Acceptance Criteria

สำหรับฟีเจอร์สำคัญให้ใช้รูปแบบ:

### AC-001: [ชื่อสถานการณ์]

- **Given:** เงื่อนไขเริ่มต้น
- **When:** การกระทำ
- **Then:** ผลลัพธ์ที่คาดหวัง

ต้องครอบคลุม Happy Path, Validation Error, Permission Denied, Duplicate Request, Timeout และ External Service Failure ตามความเหมาะสม

## 6. Non-Functional Requirements

สร้างตาราง:

| ID | Category | Requirement | Target | Measurement Method |
|---|---|---|---:|---|

ต้องพิจารณา:

- Performance และ Response Time
- Concurrent Users และ Scalability
- Availability, Backup, RTO และ RPO
- Authentication และ Authorization
- Encryption, Secret Management และ Rate Limiting
- OWASP Top 10 และ Audit Log
- Privacy/PDPA, Consent, Retention และ Data Deletion
- Usability, Accessibility และ Responsive Design
- Compatibility
- Maintainability
- Logging, Monitoring, Metrics และ Alerting

ระบุชัดเจนว่าข้อกำหนดด้านกฎหมายเป็นข้อเสนอเบื้องต้นและต้องให้ผู้เชี่ยวชาญตรวจสอบ

## 7. System Architecture and Technical Design

- เลือกรูปแบบ Architecture ที่เหมาะสม เช่น Modular Monolith, Microservices, Serverless, Event-driven หรือ IoT/Edge
- อธิบายเหตุผล ข้อดี ข้อจำกัด และแนวทางขยายระบบ
- สร้าง Mermaid High-Level Architecture Diagram
- สร้าง Mermaid Data Flow สำหรับกระบวนการหลัก

สร้างตาราง Tech Stack:

| Layer | Recommended Technology | Purpose | Reason | Alternative |
|---|---|---|---|---|

ครอบคลุม Frontend, Backend, Database, Cache, Queue, File Storage, Authentication, Cloud, Monitoring และ Testing

สร้างตาราง Technical Decision:

| Decision | Options | Selected Option | Reason | Trade-off |
|---|---|---|---|---|

## 8. Database Schema Design

- อธิบาย Database Strategy, Naming Convention, Primary Key, Index, Transaction, Timestamp และ Soft Delete
- พิจารณา Multi-tenancy หากเกี่ยวข้อง
- สร้าง Mermaid ER Diagram

สร้าง Data Dictionary:

| Table | Column | Data Type | Nullable | Key/Index | Description |
|---|---|---|---:|---|---|

สร้างตารางความสัมพันธ์:

| Parent Table | Child Table | Relationship | Foreign Key | Delete Behavior |
|---|---|---|---|---|

อธิบาย Data Lifecycle ตั้งแต่ Create, Update, Archive, Export, Retention จนถึง Delete

## 9. API and External Integrations

- กำหนด API Style, Versioning, Authentication, Pagination, Filtering, Error Format, Rate Limit และ Idempotency

สร้าง Endpoint Table:

| API ID | Method | Endpoint | Purpose | Auth | Main Errors |
|---|---|---|---|---|---|

- แสดงตัวอย่าง Request/Response JSON สำหรับ API สำคัญ 2–3 Endpoint
- ระบุ External Services, ข้อมูลที่แลกเปลี่ยน, Timeout, Retry และ Fallback
- อธิบาย Webhook Signature และ Duplicate Prevention หากเกี่ยวข้อง

## 10. UI/UX and Main Workflows

- จัดทำ Screen Inventory
- อธิบาย Information Architecture และ Navigation
- สร้าง Mermaid Workflow สำหรับ User Flow หลัก
- กำหนดสถานะ Loading, Empty, Success, Error, Permission Denied และ Offline

สร้างตาราง:

| Screen ID | Screen Name | Purpose | User Roles | Main Actions |
|---|---|---|---|---|

## 11. Testing, Deployment and Operations

### Testing Strategy

ครอบคลุม Unit, Integration, API, End-to-End, Security, Performance, UAT และ Backup/Restore Test

สร้าง Critical Test Scenarios:

| Test ID | Scenario | Expected Result | Priority | Related Requirement |
|---|---|---|---|---|

### Deployment and CI/CD

- กำหนด Local, Development, Staging และ Production
- อธิบาย Infrastructure, Domain, SSL, Database, Storage, Secrets, Monitoring และ Backup
- กำหนด Workflow: Lint → Test → Build → Security Scan → Staging → UAT → Production → Smoke Test
- ระบุ Deployment Strategy และ Rollback Plan
- แสดงเฉพาะชื่อ Environment Variables และวัตถุประสงค์ ห้ามแสดงค่าจริง

## 12. Implementation Plan

แบ่งเป็น:

- Phase 0: Discovery and Validation
- Phase 1: MVP
- Phase 2: Enhancement
- Phase 3: Scale and Optimization

สร้าง Roadmap:

| Phase | Deliverables | Dependencies | Completion Criteria | Complexity |
|---|---|---|---|---|

หากไม่มีข้อมูลเพียงพอให้ใช้ Complexity แบบ `S / M / L / XL` และไม่ต้องคาดเดาระยะเวลาแบบฟันธง

สร้าง Product Backlog:

| Backlog ID | Epic | User Story/Task | Priority | Dependency | Complexity | MVP |
|---|---|---|---|---|---|---:|

## 13. Risks, Traceability and Open Questions

สร้าง Risk Register:

| Risk ID | Risk | Probability | Impact | Mitigation | Owner |
|---|---|---|---|---|---|

สร้าง Requirement Traceability Matrix:

| Business Goal | Requirement ID | Component/API | Database Entity | Acceptance/Test ID |
|---|---|---|---|---|

สร้าง Open Questions:

| ID | Question/Decision | Why It Matters | Recommended Default | Blocking |
|---|---|---|---|---:|

## 14. Development Readiness Checklist

- [ ] Business Goal ชัดเจน
- [ ] MVP Scope ได้รับการยืนยัน
- [ ] User Roles และ Permissions ครบถ้วน
- [ ] Functional Requirements มี Acceptance Criteria
- [ ] Database Schema รองรับฟีเจอร์
- [ ] API Contract เชื่อมโยงกับ Requirements
- [ ] Security และ Privacy Requirements ได้รับการพิจารณา
- [ ] Test Strategy พร้อม
- [ ] Deployment และ Rollback Plan พร้อม
- [ ] Blocking Questions ได้รับการระบุ

---

## คำสั่งส่งออก

1. ส่งออกเป็น Markdown ทั้งหมดและเป็นเอกสารเดียว
2. เริ่มเอกสารด้วย `# System Blueprint — [Project Name]`
3. ไม่ต้องอธิบายวิธีคิดของ AI ก่อนหรือหลังเอกสาร
4. ไม่ต้องรอข้อมูลครบ หากสามารถตั้งสมมติฐานที่สมเหตุสมผลได้
5. ทำเครื่องหมายข้อมูลที่ยังไม่ยืนยันด้วย `Assumption` หรือ `TBD`
6. เอกสารต้องละเอียดพอสำหรับแบ่ง Epic, User Story, Development Task และ Test Case
7. ตรวจสอบความสอดคล้องระหว่าง Business Goal, Requirement, Database, API และ Test ก่อนส่งมอบ

---

## ตัวอย่างข้อมูลแบบสั้น

```text
Project Name: MChat

Rough Idea:
แอปบันทึกรายรับรายจ่ายผ่านแชทภาษาไทย ผู้ใช้พิมพ์ พูด หรือส่งสลิป ระบบช่วยแยกยอดเงิน หมวดหมู่ และวันที่ พร้อม Dashboard สรุปผล

Target Users:
ร้านค้าออนไลน์ เกษตรกร ฟรีแลนซ์ และธุรกิจขนาดเล็ก

Platform:
Responsive Web App

Preferred Tech Stack:
ให้ช่วยเสนอ

Document Language:
Thai
```

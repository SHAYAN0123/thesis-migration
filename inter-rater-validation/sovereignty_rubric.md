# Gate 3: Sovereignty Compliance Assessment Rubric

**Purpose:** Systematic, reproducible evaluation instrument for assessing whether a migrated system (P_{n+1}) satisfies EU digital sovereignty requirements.

**Source framework:** 7 themes derived from comparative analysis of 6 EU sovereignty frameworks (EU SEAL, CIGREF, Gaia-X, Dutch BIO, German Souveräner Cloud, French SecNumCloud).

**Scoring:** Each theme is assessed as PASS, PARTIAL, or FAIL. A system passes Gate 3 only if all 7 themes receive PASS.

**Inter-rater use:** This rubric is designed so that an independent assessor, given the same system and rubric, would reach the same verdict. Each criterion includes an observable evidence requirement — not a subjective judgment.

---

## Assessment Protocol

For each theme below:
1. Read the **criterion** (what must be true)
2. Perform the **evidence check** (what to inspect)
3. Record the **observable evidence** (what you found)
4. Assign the **verdict** (PASS / PARTIAL / FAIL) using the decision rule

---

## Theme 1: Jurisdiction

**Criterion:** The system must not depend on services governed by non-EU law. No exposure to extraterritorial legislation (e.g., US CLOUD Act, Chinese CSL).

**Evidence check:**
- [ ] List all runtime network calls made by the application
- [ ] Identify the legal jurisdiction of each external service endpoint
- [ ] Check for hard-coded API endpoints pointing to non-EU providers

**Decision rule:**
| Verdict | Condition |
|---------|-----------|
| PASS | Zero external API calls to non-EU-governed services. All network endpoints (if any) are configurable. |
| PARTIAL | External endpoints exist but are configurable (could point to EU services). |
| FAIL | Hard-coded dependency on a service governed by non-EU law. |

---

## Theme 2: Data Localisation

**Criterion:** All application data must be storable within EU borders. No hard-coded storage regions outside the EU.

**Evidence check:**
- [ ] Identify all data persistence mechanisms (databases, file storage, caches)
- [ ] Check for hard-coded cloud regions or storage endpoints
- [ ] Verify that storage location is environment-configurable

**Decision rule:**
| Verdict | Condition |
|---------|-----------|
| PASS | All data storage is local or environment-configurable with no hard-coded non-EU regions. |
| PARTIAL | Storage is configurable but defaults to a non-EU region. |
| FAIL | Data is sent to or stored in a hard-coded non-EU location. |

---

## Theme 3: Operational Autonomy

**Criterion:** The system must be operable without depending on a single cloud vendor's control plane.

**Evidence check:**
- [ ] Can the system start without connecting to any cloud provider API?
- [ ] Does deployment require a vendor-specific CLI or control plane?
- [ ] List all runtime dependencies — are any vendor-operated?

**Decision rule:**
| Verdict | Condition |
|---------|-----------|
| PASS | System runs as a standalone process with no vendor control plane required at runtime. |
| PARTIAL | System runs standalone but deployment requires a vendor-specific tool. |
| FAIL | System cannot operate without a specific cloud provider's runtime services. |

---

## Theme 4: Lock-in Avoidance

**Criterion:** No vendor-specific APIs in application code. No proprietary data formats that prevent migration.

**Evidence check:**
- [ ] Run `analyzer.py` — are there zero cloud dependencies across all 4 layers?
- [ ] Check data storage format — is it a standard format (SQL, JSON, CSV)?
- [ ] Check API interface — is it standard HTTP/REST?

**Decision rule:**
| Verdict | Condition |
|---------|-----------|
| PASS | analyzer.py reports 0 cloud dependencies (all 4 layers) AND data format is standard AND API interface is standard. |
| PARTIAL | analyzer.py reports 0 cloud deps but data format or API uses a vendor-specific convention. |
| FAIL | analyzer.py reports > 0 cloud dependencies. |

**Note:** Theme 4 is partially automated via Gate 2 (analyzer.py). This rubric item captures the broader lock-in dimensions that Gate 2 does not cover (data format, API conventions).

---

## Theme 5: Supply-Chain Control

**Criterion:** No single vendor controls the entire technology stack. Key dependencies must be replaceable.

**Evidence check:**
- [ ] List all runtime dependencies (from requirements.txt or equivalent)
- [ ] For each dependency: is it open-source? Is there an alternative?
- [ ] Is there a single vendor that controls ≥3 dependencies?

**Decision rule:**
| Verdict | Condition |
|---------|-----------|
| PASS | All runtime dependencies are open-source with known alternatives. No single vendor controls ≥3 dependencies. |
| PARTIAL | Dependencies are open-source but ≥1 has no practical alternative. |
| FAIL | A proprietary dependency with no alternative exists, or a single vendor controls the stack. |

---

## Theme 6: Openness & Standards

**Criterion:** The system should use open standards and protocols. Prefer open-source over proprietary.

**Evidence check:**
- [ ] List communication protocols used (HTTP, gRPC, AMQP, etc.)
- [ ] List data exchange formats (JSON, XML, Protobuf, etc.)
- [ ] List database interfaces (SQL, key-value, document, etc.)
- [ ] Are all of the above open standards?

**Decision rule:**
| Verdict | Condition |
|---------|-----------|
| PASS | All protocols, data formats, and database interfaces are open standards (HTTP, SQL, JSON, etc.). |
| PARTIAL | Core interfaces are open but ≥1 uses a non-standard extension. |
| FAIL | A proprietary protocol, format, or interface is required for core functionality. |

---

## Theme 7: Sustainability

**Criterion:** The system must be maintainable and portable long-term without vendor cooperation.

**Evidence check:**
- [ ] Can the system be built from source without vendor-provided build tools?
- [ ] Are all dependencies available from public package registries?
- [ ] Is there a risk of vendor-controlled deprecation?
- [ ] Could the system be maintained by a different team without vendor support?

**Decision rule:**
| Verdict | Condition |
|---------|-----------|
| PASS | System builds from source with standard tools, all deps are on public registries, no vendor deprecation risk. |
| PARTIAL | System builds from source but ≥1 dependency is maintained by a single entity with no fork/alternative. |
| FAIL | System requires a vendor-controlled service or tool that could be unilaterally deprecated. |

---

## Summary Sheet

| Theme | Criterion (short) | Verdict | Evidence |
|-------|-------------------|---------|----------|
| 1. Jurisdiction | No non-EU service dependencies | | |
| 2. Data Localisation | Data storable in EU | | |
| 3. Operational Autonomy | No vendor control plane | | |
| 4. Lock-in Avoidance | No vendor APIs + standard formats | | |
| 5. Supply-Chain Control | Replaceable dependencies | | |
| 6. Openness & Standards | Open protocols and formats | | |
| 7. Sustainability | Long-term maintainability | | |

**Gate 3 Verdict:** PASS only if all 7 themes = PASS.

---

## Relationship to Other Gates

- **Gate 1** (behavioral fitness function): Verifies specification-bounded semantic equivalence via test suite. Independent of sovereignty.
- **Gate 2** (structural fitness function): Partially automates Theme 4 (lock-in avoidance) via dependency detection. Gate 3 extends this with the non-automatable dimensions.
- **Gate 3** (compliance fitness function): This rubric. Covers all 7 sovereignty themes. Semi-automated (Theme 4 uses Gate 2 output; remaining themes require assessor judgment).

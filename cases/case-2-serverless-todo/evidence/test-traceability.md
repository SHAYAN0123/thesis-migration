# Test-to-Specification Traceability Matrix — Case Study 2

Every test in `test_api.py` is derived from a specific clause in `spec/api_spec.md`.
This document provides the full mapping.

**Total tests: 43**
**Spec sections traced: Data Model (5 fields), 5 API Endpoints, 8 Behavior Rules**

---

## POST /todos — Create a Todo (10 tests)

| # | Test | Spec Clause |
|---|------|-------------|
| 1 | `test_create_returns_200` | "Status: 200" |
| 2 | `test_create_response_is_json` | "Returns: the created todo as JSON" |
| 3 | `test_create_response_contains_id` | Data model: "id: string, required" |
| 4 | `test_create_id_is_non_empty_string` | Data model: "id: string, required, Unique identifier (UUID)" |
| 5 | `test_create_id_is_valid_uuid` | Data model: "Unique identifier (UUID)" |
| 6 | `test_create_text_is_stored` | Data model: "text: string, required, The todo content" |
| 7 | `test_create_checked_defaults_to_false` | Behavior Rule 2: "Every created todo MUST have checked set to false by default" |
| 8 | `test_create_has_created_at` | Data model: "createdAt: string, required, Timestamp when created" |
| 9 | `test_create_has_updated_at` | Data model: "updatedAt: string, required, Timestamp when last updated" |
| 10 | `test_create_without_text_returns_error` | "Request body: JSON with text field (required)" |

## GET /todos — List All Todos (6 tests)

| # | Test | Spec Clause |
|---|------|-------------|
| 11 | `test_list_returns_200` | "Status: 200" |
| 12 | `test_list_response_is_json` | "Returns: JSON array of all todos" (JSON implies JSON content type) |
| 13 | `test_list_returns_array` | "Returns: JSON array of all todos" |
| 14 | `test_list_is_empty_before_any_create` | "Returns: JSON array of all todos" (no todos → empty array) |
| 15 | `test_list_contains_created_todo` | Behavior Rule 7: "Listing todos MUST return ALL existing todos" |
| 16 | `test_list_returns_all_todos` | Behavior Rule 7: "Listing todos MUST return ALL existing todos" (multiple items) |

## GET /todos/{id} — Get a Single Todo (5 tests)

| # | Test | Spec Clause |
|---|------|-------------|
| 17 | `test_get_one_returns_200` | "Status: 200" |
| 18 | `test_get_one_response_is_json` | "Returns: the todo matching the given ID as JSON" |
| 19 | `test_get_one_returns_correct_todo` | "Returns: the todo matching the given ID" |
| 20 | `test_get_one_returns_all_five_fields` | Data model: all 5 fields (id, text, checked, createdAt, updatedAt) are required |
| 21 | `test_get_one_returns_404_for_unknown_id` | "If not found: returns error (status 404 or equivalent)" |

## PUT /todos/{id} — Update a Todo (9 tests)

| # | Test | Spec Clause |
|---|------|-------------|
| 22 | `test_update_returns_200` | "Status: 200" |
| 23 | `test_update_response_is_json` | "Returns: the updated todo attributes as JSON" |
| 24 | `test_update_text_is_changed` | "Updates the todo's text" |
| 25 | `test_update_checked_can_be_set_to_true` | "Updates the todo's checked status" |
| 26 | `test_update_checked_can_be_toggled_back_to_false` | "Updates the todo's checked status" (bidirectional) |
| 27 | `test_update_response_includes_updated_at` | "Returns: the updated todo attributes as JSON" (must include updatedAt) |
| 28 | `test_update_changes_updated_at_timestamp` | Behavior Rule 4: "Updating a todo MUST change the updatedAt timestamp" |
| 29 | `test_update_does_not_change_id` | Behavior Rule 5: "Updating a todo MUST NOT change the id" |
| 30 | `test_update_does_not_change_created_at` | Behavior Rule 5: "Updating a todo MUST NOT change the createdAt" |

## DELETE /todos/{id} — Delete a Todo (4 tests)

| # | Test | Spec Clause |
|---|------|-------------|
| 31 | `test_delete_returns_200` | "Status: 200" |
| 32 | `test_delete_subsequent_get_returns_404` | Behavior Rule 6: "subsequent GET returns not found" |
| 33 | `test_delete_removes_todo_from_list` | Behavior Rule 6: "Deleting a todo MUST remove it permanently" (not in list) |
| 34 | `test_delete_does_not_affect_other_todos` | Implicit: delete is scoped to the specified ID |

## Behavior Rules — Dedicated Tests (9 tests)

These tests re-verify the 8 spec behavior rules as standalone assertions.
Some overlap with endpoint tests above — this is intentional redundancy to ensure each rule has a dedicated, named test.

| # | Test | Spec Clause |
|---|------|-------------|
| 35 | `test_spec_rule_1_ids_are_unique_uuids` | Rule 1: "Every created todo MUST have a unique UUID as its id" (5 items, all unique, all valid UUIDs) |
| 36 | `test_spec_rule_2_checked_is_false_by_default` | Rule 2: "Every created todo MUST have checked set to false by default" (3 items) |
| 37 | `test_spec_rule_3_timestamps_recorded_on_create` | Rule 3: "Every created todo MUST record createdAt and updatedAt timestamps" |
| 38 | `test_spec_rule_4_updated_at_changes_on_update` | Rule 4: "Updating a todo MUST change the updatedAt timestamp" |
| 39 | `test_spec_rule_5_id_immutable_after_update` | Rule 5: "Updating a todo MUST NOT change the id" |
| 40 | `test_spec_rule_5_created_at_immutable_after_update` | Rule 5: "Updating a todo MUST NOT change the createdAt" |
| 41 | `test_spec_rule_6_delete_is_permanent` | Rule 6: "Deleting a todo MUST remove it permanently" (both GET and LIST) |
| 42 | `test_spec_rule_7_list_returns_all_existing_todos` | Rule 7: "Listing todos MUST return ALL existing todos" (4 items) |
| 43 | `test_spec_rule_8_data_persists_between_requests` | Rule 8: "The service MUST persist data between requests" |

---

## Coverage Summary

| Spec Section | Clauses | Tests | Coverage |
|-------------|---------|-------|----------|
| POST /todos | 6 (status, JSON, id, text, checked, timestamps, text required) | 10 | Complete |
| GET /todos | 3 (status, JSON array, returns all) | 6 | Complete |
| GET /todos/{id} | 4 (status, JSON, correct item, 5 fields, 404) | 5 | Complete |
| PUT /todos/{id} | 6 (status, JSON, text, checked, updatedAt, immutability) | 9 | Complete |
| DELETE /todos/{id} | 3 (status, permanent removal, scoped) | 4 | Complete |
| Behavior Rules 1–8 | 8 rules (Rule 5 has 2 sub-clauses) | 9 | Complete |
| **Total** | | **43** | **Complete w.r.t. specification** |

---

## What Is NOT Covered (honest limitations)

These are behaviors NOT in the spec and therefore NOT tested:

- Concurrent access (two clients writing simultaneously)
- Performance under load
- Input validation beyond missing `text` field (e.g., max length, special characters)
- Authentication / authorization
- Pagination for large lists
- CORS headers
- Error response body format (only status codes are specified)

This is by design: the equivalence claim is bounded by the specification, not by all possible behaviors.

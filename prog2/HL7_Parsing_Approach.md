**General HL7 Parsing Approach**

HL7 messages are structured text, with segments (lines starting with 3-letter codes like MSH, PID, OBX) delimited by carriage returns. Within segments, fields are delimited by `|` (pipe), components by `^` (caret), sub-components by `&` (ampersand), and repetitions by `~` (tilde).

The general process for each message involves:
1.  **Splitting the message into segments.**
2.  **For each segment, splitting it into fields.**
3.  **For complex fields, further splitting them into components and sub-components.**
4.  **Mapping these parts to meaningful JSON keys.** Standard HL7 field names and descriptions should guide the naming of JSON keys for clarity.
5.  **Handling data types:** Dates and times should be standardized (e.g., to ISO 8601). Numerical values should be stored as numbers in JSON if possible.

The following descriptions and JSON structures illustrate the mapping logic.

---

**1. MDM (Medical Document Management - from `datiORB1.txt`)**

MDM messages are typically used for transmitting medical documents or metadata about them. The `MDM^T01` message, as in your example, often conveys information about a document, its patient, and related encounter.

**Key Segments and Information Extraction:**

*   **MSH (Message Header):** Contains metadata about the message itself.
    *   `MSH-3`: Sending Application
    *   `MSH-4`: Sending Facility
    *   `MSH-5`: Receiving Application
    *   `MSH-6`: Receiving Facility
    *   `MSH-7`: Date/Time of Message
    *   `MSH-9`: Message Type (e.g., `MDM^T01^MDM_T01` gives overall type, event, and structure)
    *   `MSH-10`: Message Control ID
    *   `MSH-12`: Version ID
*   **EVN (Event Type):** Details about the event that triggered the message.
    *   `EVN-2`: Recorded Date/Time (when the event occurred or was logged)
*   **PID (Patient Identification):** Information about the patient.
    *   `PID-3`: Patient Identifier List (can be multiple IDs, like medical record number, fiscal code). Each ID has components: ID number, assigning authority, identifier type code.
    *   `PID-5`: Patient Name (family name, given name, etc.)
    *   `PID-7`: Date/Time of Birth
    *   `PID-8`: Administrative Sex
    *   `PID-11`: Patient Address (can be multiple addresses, each with components like street, city, zip, type).
*   **PV1 (Patient Visit):** Information about a specific patient encounter.
    *   `PV1-2`: Patient Class (e.g., Inpatient, Outpatient)
    *   `PV1-3`: Assigned Patient Location (department, room, bed)
    *   `PV1-19`: Visit Number (an identifier for the visit)
*   **TXA (Transcription Document Header):** Metadata about the transcribed document.
    *   `TXA-2`: Document Type
    *   `TXA-6`: Activity Date/Time (related to the document creation/activity)
    *   `TXA-9`: Originator(s) (e.g., doctor who authored/dictated the document)
    *   `TXA-12`: Unique Document Number
    *   `TXA-13`: Parent Document Number (if applicable)
    *   `TXA-16`: Document Completion Status
    *   `TXA-17`: Document Confidentiality Status
    *   `TXA-19`: Document Availability Status
    *   `TXA-22`: Unique Document File Name or Identifier

**Proposed JSON Structure for MDM:**
```json
{
  "message_metadata": {
    "type": "MDM",
    "trigger_event": "T01",
    "structure": "MDM_T01",
    "sending_application": "XXX",
    "sending_facility": "XXX",
    "receiving_application": "YYY",
    "receiving_facility": "YYY",
    "datetime_of_message": "20250530153555",
    "message_control_id": "96a084d8-18fc-4d38-8258-bd6936efe699",
    "version_id": "2.5"
  },
  "event_information": {
    "recorded_datetime": "20250530153555"
  },
  "patient_identification": {
    "identifiers": [
      { "id_number": "1721260", "assigning_authority": { "namespace_id": "PK" }, "identifier_type_code": "PI" },
      { "id_number": "CODICEFISCALE", "assigning_authority": { "namespace_id": "NNITA" }, "identifier_type_code": "CF" }
    ],
    "name": {
      "family_name": "COGNOME",
      "given_name": "NOME",
      "name_type_code": "L"
    },
    "date_of_birth": "19331008",
    "administrative_sex": "F",
    "addresses": [
      {
        "street_address": "VIA DI RESIDENZA",
        "city": "DECS. COMUNE",
        "zip_or_postal_code": "CAP",
        "address_type": "L"
      },
      {
        "city": "DESC. COMUNE",
        "state_or_province": "COD.COMUNE", // Assuming COD.COMUNE is State/Province here
        "country": "CITTADINANZA", // Assuming CITTADINANZA is Country
        "address_type": "BDL"
      }
    ]
  },
  "patient_visit": {
    "patient_class": "I",
    "assigned_location": {
      "point_of_care": "COD.REPARTO", // From PV1-3.1
      "description": "DESC. REPARTO" // From PV1-3.9
    },
    "visit_number": {
      "id_number": "NOSOLOGICO", // From PV1-19.1
      "assigning_facility": { "namespace_id":"identificativo referto" } // From PV1-19.4
    }
  },
  "document_header": {
    "set_id": "1",
    "document_type": "ZZZ",
    "activity_datetime": "20250530132243",
    "originators": [
      {
        "id_number": "COD.FISCALEMEDICO",
        "family_name": "NOMINATIVO MEDICO",
        "identifier_type_code": "CF"
      }
    ],
    "unique_document_number": "2.16.840.1.113883.2.9.2.70.4.4\\S\\103.200310291948",
    "parent_document_number": "CPOE279695",
    "document_completion_status": "LA",
    "document_confidentiality_status": "N",
    "document_availability_status": "OR",
    "unique_document_filename": "2.22.222.2.222222.2.2.2.22222.2.2.2.2"
  }
}
```

---

**2. OUL (Unsolicited Laboratory Observation - from `datiORB2.txt`)**

OUL messages are used to send laboratory results from the lab system to other clinical systems. `OUL^R22` specifically is for unsolicited transmission of observation results.

**Key Segments and Information Extraction:**

*   **MSH (Message Header):** Similar to MDM. `MSH-9` will be `OUL^R22`.
*   **PID (Patient Identification):** Similar to MDM. Also includes:
    *   `PID-13`: Phone Number
    *   `PID-18`: Patient Account Number
    *   `PID-19`: SSN Number - Patient
*   **SPM (Specimen):** Describes the specimen used for the tests. An OUL message can contain multiple SPM segments if results for different specimens are being sent.
    *   `SPM-2`: Specimen ID (often the lab's unique ID for the sample)
    *   `SPM-4`: Specimen Type (e.g., Siero, Plasma, Urine)
    *   `SPM-17`: Specimen Collection Date/Time
*   **OBR (Observation Request):** Defines a test or a battery of tests ordered. There can be multiple OBR segments, often one for each test panel or order, typically grouped under an SPM segment.
    *   `OBR-2`: Placer Order Number (from the ordering system)
    *   `OBR-3`: Filler Order Number (from the lab system)
    *   `OBR-4`: Universal Service Identifier (code for the test/battery, e.g., LOINC or local code)
    *   `OBR-7`: Observation Date/Time (often specimen collection or receipt time)
    *   `OBR-22`: Results Rpt/Status Chng - Date/Time
    *   `OBR-25`: Result Status (e.g., Final, Preliminary, Corrected)
*   **ORC (Common Order):** Paired with OBR, provides general order information.
    *   `ORC-1`: Order Control (e.g., NW for New Order, RE for Results)
    *   `ORC-5`: Order Status
    *   `ORC-9`: Date/Time of Transaction
    *   `ORC-21`: Ordering Facility
*   **TQ1 (Timing/Quantity):** Provides timing information for the order. (Optional, can be multiple)
    *   `TQ1-7`: Start Date/Time
*   **OBX (Observation/Result):** Contains individual results for a test defined in the preceding OBR. There will be one OBX for each distinct observation/result.
    *   `OBX-2`: Value Type (e.g., NM for Numeric, CE for Coded Entry, TX for Text)
    *   `OBX-3`: Observation Identifier (code for the specific test result)
    *   `OBX-5`: Observation Value (the actual result)
    *   `OBX-6`: Units
    *   `OBX-7`: Reference Range
    *   `OBX-8`: Abnormal Flags (e.g., H for High, L for Low, N for Normal)
    *   `OBX-11`: Observation Result Status (e.g., F for Final, C for Corrected)
    *   `OBX-14`: Date/Time of the Observation (when the result was generated)
    *   `OBX-16`: Responsible Observer (e.g., ID of the performing technologist or lab section)

**Proposed JSON Structure for OUL:**
```json
{
  "message_metadata": {
    "type": "OUL",
    "trigger_event": "R22",
    "sending_application": "XXX",
    "sending_facility": "XXX",
    "receiving_application": "YYY",
    "receiving_facility": "YYY",
    "datetime_of_message": "20250530154128",
    "message_control_id": "1768820250530154128",
    "version_id": "2.5"
  },
  "patient_identification": {
    "identifiers": [
      { "id_number": "383378", "assigning_authority": { "namespace_id": "CS" }, "identifier_type_code": "SS" },
      { "id_number": "46630100", "assigning_authority": { "namespace_id": "ZZZ" }, "identifier_type_code": "ZZZ" },
      { "id_number": "630110", "assigning_authority": { "namespace_id": "BDA" }, "identifier_type_code": "PI" },
      { "id_number": "CODICEFISCALE", "assigning_authority": { "namespace_id": "NN" }, "identifier_type_code": "CF" }
    ],
    "name": { "family_name": "COGNOME", "given_name": "NOME" },
    "date_of_birth": "19780319",
    "administrative_sex": "F",
    "addresses": [
      {
        "street_address": "VIA DI RESIDENZA",
        "city": "DESC.COMUNE",
        "zip_or_postal_code": "CAP",
        "address_type": "L",
        "other_geographic_designation": "COD.COMUNE"
      },
      {
        "city": "COD.COMUNE", // PID-11.3 for the second address
        // Assuming COD.COMUNE from PID-11.8 (other geographic designation) for the second repetition
        "other_geographic_designation": "COD.COMUNE"
      }
    ],
    "phone_numbers": [
      {
        "telephone_number_unformatted": "RECAPITO TEL", // PID-13.7
        "telecommunication_use_code": "PRN",           // PID-13.2
        "telecommunication_equipment_type": "PH",      // PID-13.3
        "country_code_phone": "y"                      // PID-13.8 - Unusual value
      }
    ],
    "patient_account_number": "CPDICEFISCALE", // PID-18
    "ssn_number": "383378",                  // PID-19
    "ethnic_group": [{"identifier": "COD.COMUNE"}],    // PID-22
    "nationality": {"identifier": "CITTADINANZA"},  // PID-28
    "production_class_code": {"text": "N"},           // PID-33
    "birth_too_early": {"value": "N"}               // PID-34
  },
  "specimens": [ // An array because a message might contain multiple specimens
    {
      "specimen_id": "312713635143",
      "type": { "identifier": "SI", "text": "Siero" },
      "collection_datetime": "20250530150000",
      "lab_orders": [ // Array for OBRs related to this specimen
        // Example for "EMOLISI" order
        {
          "set_id_obr": "1",
          "filler_order_number": { "entity_identifier": "3127136351", "namespace_id": "DN", "universal_id": "1-3127136351-20250530150000" },
          "universal_service_identifier": { "identifier": "11", "text": "EMOLISI", "name_of_coding_system": "V", "alternate_identifier": "11@1", "name_of_alternate_coding_system": "DN" },
          "observation_request_datetime": "20250530150000", // OBR-7
          "result_status_obr": "I", // OBR-25
          "diagnostic_service_section_id": "ZZZ-1", // OBR-24
          "results_status_change_datetime": "20250530150000", // From OBR-22 (Time Of An Event subcomponent)
          "order_control": { // From associated ORC segment
            "code": "NW",
            "placer_group_number": { "entity_identifier": "7596998", "namespace_id": "DN" },
            "order_status": "IP",
            "transaction_datetime": "20250530154128",
            "ordering_facility": { "organization_name": "DESC. REPARTO INVIANTE", "identifier_type_code": "FI", "id_number": "COD.REPARTOI NVIANTE" }
          },
          "timing_quantity": [{ // From TQ1
            "set_id_tq1": "1",
            "start_datetime": "20250530150000",
            "condition_text": "S"
          }],
          "results": [ // Array for OBX segments related to this OBR
            {
              "set_id_obx": "1",
              "value_type": "CE",
              "observation_identifier": { "identifier": "11", "text": "EMOLISI", "name_of_coding_system": "V", "alternate_identifier": "11@1", "name_of_alternate_coding_system": "DN" },
              "value": "11",
              "result_status_obx": "I",
              "observation_datetime": "20250530153700"
              // Units, reference range, abnormal flags, responsible observer would be here if present
            }
          ]
        },
        // ... (other lab_orders for ITTERO, LIPEMIA, POTASSIO, SODIO would follow similar structure)
        // For POTASSIO example result:
        {
          "set_id_obr": "4",
          "placer_order_number": {"entity_identifier": "30614490"}, // OBR-2
          "filler_order_number": { "entity_identifier": "3127136351", "namespace_id": "DN", "universal_id": "1-3127136351-20250530150000" },
          "universal_service_identifier": { "identifier": "0017", "text": "POTASSIO", "name_of_coding_system": "V", "alternate_identifier": "0017@1", "name_of_alternate_coding_system": "DN" },
          "observation_request_datetime": "20250530150000",
          "result_status_obr": "I",
          // ... (ORC, TQ1 data) ...
          "results": [
            {
              "set_id_obx": "1",
              "value_type": "CE", // The example says CE, though for a numeric value like 3.9, NM would be typical.
              "observation_identifier": { "identifier": "0017", "text": "POTASSIO", "name_of_coding_system": "V", "alternate_identifier": "0017@1", "name_of_alternate_coding_system": "DN" },
              "value": "3.9",
              "units": { "identifier":"mmol/L" },
              "reference_range": "3.5 - 5.3",
              "abnormal_flags": ["N"], // Stored as array, even if one
              "result_status_obx": "I",
              "observation_datetime": "20250530153700",
              "responsible_observer": [{"person_identifier": "MAMIELE"}]
            }
          ]
        }
        // ... more orders
      ]
    }
  ]
}
```

---

**3. ORU (Unsolicited Observation Result - from `datiORB3_DOM.txt`)**

ORU messages are general observation result messages, often used for data from medical devices (like patient monitors), imaging studies, or other non-lab observations. `ORU^R01` is a common type.

**Key Segments and Information Extraction:**

*   **MSH (Message Header):** Similar structure. `MSH-9` will be `ORU^R01^ORU_R01`.
    *   `MSH-3`: Sending Application (e.g., `BM5LP` from `^BM5LP`)
*   **PID (Patient Identification):** Patient details. Can be minimal if the device focuses on measurements rather than full demographics.
    *   `PID-3`: Patient Identifier (`ttttt` in the example)
    *   `PID-7`: Date/Time of Birth
    *   `PID-8`: Administrative Sex
*   **PV1 (Patient Visit):** Visit/encounter information, if relevant. (Optional in some ORU profiles)
    *   `PV1-2`: Patient Class (or Type) (`PRIMIS_BM5_PRO` in example)
    *   `PV1-3`: Assigned Patient Location (e.g., `^^1` meaning Bed "1")
*   **ORC (Common Order):** Usually present to group observations, even if minimal.
    *   `ORC-1`: Order Control (`NW` in example)
*   **OBR (Observation Request):** Groups a set of related observations (OBX segments). For device data, one OBR might cover all parameters measured at a point in time or over a short period.
    *   `OBR-7`: Observation Date/Time (start of observation period)
    *   `OBR-8`: Observation End Date/Time (end of observation period)
*   **OBX (Observation/Result):** Each OBX carries a single observation/measurement. There will be many OBX segments for device data reporting multiple parameters.
    *   `OBX-2`: Value Type (example uses `TX` for Text Data, even for numeric values like SpO2. Ideally, `NM` for Numeric for better processing.)
    *   `OBX-3`: Observation Identifier (e.g., `HR` for Heart Rate, `SpO2-%`). Often text or local codes.
    *   `OBX-5`: Observation Value
    *   `OBX-6`: Units
    *   `OBX-7`: Reference Range
    *   `OBX-8`: Abnormal Flags (`F` in the example - interpretation depends on the sending system; might mean "Final" or a generic flag. Standard flags are H, L, N, etc.)

**Proposed JSON Structure for ORU:**
```json
{
  "message_metadata": {
    "type": "ORU",
    "trigger_event": "R01",
    "structure": "ORU_R01",
    "sending_application": "BM5LP", // From MSH-3.2
    // Sending/Receiving facility not present in example MSH
    "datetime_of_message": "20250530180220",
    "message_control_id": "BIONET PM", // Using MSH-10 as is
    "version_id": "2.4"
  },
  "patient_identification": {
    "identifiers": [
      { "id_number": "ttttt" } // No type/authority provided in example
    ],
    // Name not provided
    "date_of_birth": "18990101",
    "administrative_sex": "M"
  },
  "patient_visit": { // Minimal, based on example
    "patient_class": "PRIMIS_BM5_PRO", // PV1-2
    "assigned_location": {
      "bed": "1" // From PV1-3.3
    }
  },
  "observation_report": [ // ORU R01 can have repeating PATIENT_RESULT, each with OBRs. Assuming one set here.
    {
      "order_control": "NW", // From ORC-1
      "observation_request": { // Data from OBR segment
        "observation_start_datetime": "20250530180220", // OBR-7
        "observation_end_datetime": "20250530180220",   // OBR-8
        "observations": [ // Array of OBX segments
          {
            // Set ID OBX not present in example
            "value_type": "TX",
            "identifier": { "text": "HR" }, // OBX-3.2
            "value": null, // OBX-5 is empty
            "units": { "text": "BPM" }, // OBX-6.1 or OBX-6.2
            "reference_range": "50-150",
            "abnormal_flags": ["F"]
          },
          {
            "value_type": "TX",
            "identifier": { "text": "ST" },
            "value": null,
            "units": { "text": "MV" },
            "reference_range": "-0.40-0.40",
            "abnormal_flags": ["F"]
          },
          {
            "value_type": "TX",
            "identifier": { "text": "PVC" },
            "value": null,
            "units": null,
            "reference_range": "0-20",
            "abnormal_flags": ["F"]
          },
          {
            "value_type": "TX",
            "identifier": { "text": "SpO2-%" },
            "value": "98",
            "units": { "text": "%" },
            "reference_range": "90-100",
            "abnormal_flags": ["F"]
          }
          // ... (structure repeated for SpO2-R, PI, RR, APNEA, TEMP1, TEMP2, TEMP-DT, IBP1-S, IBP1-M, IBP1-D, IBP1-PR, IBP2-M)
        ]
      }
    }
  ]
}
```

**Key Considerations for the Framework:**

*   **Clear JSON Keys:** Employ descriptive keys in your JSON, often derived from HL7 field names or common healthcare terminology.
*   **Data Type Conversion:** Convert HL7 data types to appropriate JSON types (e.g., HL7 DTM to ISO 8601 date-time strings, HL7 NM to JSON numbers). The ORU example's use of `TX` for numeric data will require careful handling if numeric operations are needed later.
*   **Repetitions and Hierarchy:** Use JSON arrays for HL7 repeating fields/segments (like multiple `PID-3` identifiers or multiple `OBX` segments) and nested JSON objects to represent the hierarchical structure of HL7 messages (e.g., OBX results nested under an OBR order).
*   **Code Mappings:** For coded values (like in CE data types), store the code, text representation, and coding system if available (e.g., `{"identifier": "SI", "text": "Siero", "coding_system": "L"}`).
*   **Extensibility:** Design the framework to be adaptable to custom segments (Z-segments) or variations in HL7 usage, perhaps through configurable mapping rules.

This approach provides a structured way to transform HL7 data into a more queryable and interpretable JSON format for use with MongoDB or other systems.
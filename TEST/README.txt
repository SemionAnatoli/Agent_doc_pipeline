DocFlow — Test Files
====================

01_invoice_CRM_MATCH_full_success.pdf
  Expected: All 5 pipeline steps GREEN.
  INN 7812014560 (AO Neva Logistik) is in CRM.
  3 dates, 6 amounts, 2 INN candidates extracted.

02_invoice_INN_NOT_IN_CRM_review_required.pdf
  Expected: Steps 1-4 complete, Route = 'Review required'.
  INN 9999012345 is NOT in CRM -> sent to CRM enrichment queue.

03_contract_gazprom_CRM_MATCH.pdf
  Expected: All 5 steps GREEN. Document type = Contract.
  INN 7736050003 (PJSC Gazprom) matched.

04_reconciliation_act_multi_entity.pdf
  Expected: All 5 steps GREEN. Rich extraction:
  7 dates, 8+ amounts, 2 INN (Yandex + Megafon) both in CRM.

How to test:
  1. Start the server: double-click start_web.vbs
  2. Open http://127.0.0.1:8000/
  3. Drop any file above into the upload area.
  4. Watch the pipeline run step by step.

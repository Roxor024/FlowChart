# SAP consignment safety examples

This is **pure Python, synthetic and offline**. It is not an SAP adapter, a Logic App workflow or a verified Dataverse connector.

`safety.py` demonstrates exactly which business states should block setting Dataverse `Synced`:
- A SAP BAPI warning plus a document number is not proof of committed creation.
- Require explicit commit confirmation and read-back when the BAPI contract warrants it; inspect RETURN for errors.
- Match SAP translations only to active, explicitly mapped Dataverse languages; never guess LCIDs or silently pick a duplicate ISO row.
- A zero-language overlap is an exception requiring review, not an automatic success.
- SAP verification and all required Dataverse translations must succeed before marking Synced.

Microsoft Learn: https://learn.microsoft.com/en-us/azure/logic-apps/connectors/sap

Run offline tests with `python -m unittest discover -s tests -v` from the repository root.

Actual integration needs the supplied SAP WSDL or BAPI interface contract, language-code mapping, Dataverse table schema and an authorized test environment.

"""Synthetic safety reference only: no SAP/Dataverse network calls or WSDL mapping."""
from __future__ import annotations

class LanguageMappingError(ValueError):
    pass

def sap_creation_state(messages, document_id, *, commit_confirmed=False, readback_confirmed=False):
    """Never infer a committed consignment merely from a BAPI document number."""
    types = {str(m.get("TYPE", "")).upper() for m in messages}
    if types & {"E", "A", "X"}:
        return "REJECTED"
    if not document_id:
        return "NEEDS_VERIFICATION"
    if "W" in types and not commit_confirmed:
        return "NEEDS_VERIFICATION"
    if not (commit_confirmed and readback_confirmed):
        return "NEEDS_VERIFICATION"
    return "SAP_VERIFIED"

def eligible_translations(sap_rows, dv_rows):
    """Return SAP translations joined to explicitly mapped active DV languages.

    sap row: {sapLanguage, isoCode, text}; DV row: {id, sapLanguage?, isoCode?, active}.
    A bare LCID is not automatically translated to a SAP/ISO language.
    """
    result, omitted = [], []
    for row in sap_rows:
        key = row.get("sapLanguage")
        iso = row.get("isoCode")
        if not key and not iso:
            raise LanguageMappingError("SAP language key and ISO language missing")
        active = [d for d in dv_rows if d.get("active") is True]
        candidates = ([d for d in active if key and d.get("sapLanguage") == key]
                      if any(key and d.get("sapLanguage") == key for d in active)
                      else [d for d in active if iso and d.get("isoCode") == iso])
        if len(candidates) > 1:
            raise LanguageMappingError(f"ambiguous mapping for SAP language {key!r} / ISO {iso!r}")
        if not candidates:
            omitted.append({"sapLanguage": key, "isoCode": iso, "reason": "not mapped to active Dataverse language"})
            continue
        result.append({"dataverseLanguageId": candidates[0]["id"], "sapLanguage": key, "text": row["text"]})
    if not result:
        raise LanguageMappingError("zero matched Dataverse languages: verify catalog or confirm explicit no-overlap policy")
    if len({r["dataverseLanguageId"] for r in result}) != len(result):
        raise LanguageMappingError("multiple SAP translations map to one Dataverse language")
    return result, omitted

def can_mark_synced(sap_state, translations_applied, pending_failures):
    """Do not claim Synced when SAP or Dataverse updates are unverified."""
    return sap_state == "SAP_VERIFIED" and translations_applied and not pending_failures

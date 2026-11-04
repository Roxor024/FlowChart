import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples" / "sap-consignment-safety"))
from safety import sap_creation_state, eligible_translations, can_mark_synced, LanguageMappingError

class SapSafetyExample(unittest.TestCase):
    def test_warning_document_number_not_committed(self):
        self.assertEqual(sap_creation_state([{"TYPE":"W"}],"0000123"), "NEEDS_VERIFICATION")
    def test_warning_explicit_commit_and_readback(self):
        self.assertEqual(sap_creation_state([{"TYPE":"W"}],"0000123",commit_confirmed=True,readback_confirmed=True), "SAP_VERIFIED")
    def test_error_never_committed(self):
        self.assertEqual(sap_creation_state([{"TYPE":"E"}],"0000123",commit_confirmed=True,readback_confirmed=True), "REJECTED")
    def test_missing_readback_prevents_synced(self):
        self.assertEqual(sap_creation_state([],"0000123",commit_confirmed=True), "NEEDS_VERIFICATION")
        self.assertFalse(can_mark_synced("NEEDS_VERIFICATION",True,False))
    def test_intersection_and_omissions(self):
        sap=[{"sapLanguage":"E","isoCode":"EN","text":"Manual"},{"sapLanguage":"D","isoCode":"DE","text":"Anleitung"}]
        dv=[{"id":"dv-en","sapLanguage":"E","isoCode":"EN","active":True},{"id":"dv-nl","sapLanguage":"N","isoCode":"NL","active":True}]
        selected, omitted=eligible_translations(sap,dv)
        self.assertEqual([s["dataverseLanguageId"] for s in selected],["dv-en"])
        self.assertEqual(len(omitted),1)
    def test_duplicate_iso_ambiguity(self):
        sap=[{"sapLanguage":None,"isoCode":"EN","text":"Manual"}]
        dv=[{"id":"en-US","isoCode":"EN","active":True},{"id":"en-GB","isoCode":"EN","active":True}]
        with self.assertRaises(LanguageMappingError):eligible_translations(sap,dv)
    def test_sap_key_disambiguates_iso(self):
        sap=[{"sapLanguage":"E","isoCode":"EN","text":"Manual"}]
        dv=[{"id":"en-US","sapLanguage":"E","isoCode":"EN","active":True},{"id":"en-GB","sapLanguage":"B","isoCode":"EN","active":True}]
        selected,_=eligible_translations(sap,dv)
        self.assertEqual(selected[0]["dataverseLanguageId"],"en-US")
    def test_zero_matches_fails_loudly(self):
        with self.assertRaises(LanguageMappingError):eligible_translations([{"sapLanguage":"D","isoCode":"DE","text":"Text"}],[{"id":"nl","isoCode":"NL","active":True}])
    def test_lcid_without_mapping_does_not_guess(self):
        with self.assertRaises(LanguageMappingError):eligible_translations([{"sapLanguage":"E","isoCode":"EN","text":"Manual"}],[{"id":"1033","lcid":1033,"active":True}])
    def test_not_synced_if_translation_update_failed(self):
        self.assertFalse(can_mark_synced("SAP_VERIFIED",True,True))

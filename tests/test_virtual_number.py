"""Acceptance tests for source-derived, non-spoofing Virtual Number features."""
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from services.gateway.app import app
from services.virtual_number.vanity import (
    classify_alias, digits_only, e164_syntax, filter_verified_carrier_inventory,
    suggest_internal_aliases,
)


class VanityTests(unittest.TestCase):
    def test_platinum_all_same_and_repeated_blocks(self):
        self.assertEqual(classify_alias("777 777 777").tier, "PLATINUM")
        self.assertEqual(classify_alias("12 12 12 12").tier, "GOLD")

    def test_custom_prefix_is_preserved_and_no_provider_availability_claimed(self):
        for prefix in ("111", "000", "798", "62"):
            rows = suggest_internal_aliases(prefix=prefix, length=10, count=8)
            self.assertEqual(len(rows), 8)
            self.assertEqual(len(set(r.identifier for r in rows)), 8)
            self.assertTrue(all(r.identifier.startswith(prefix) for r in rows))
            self.assertTrue(all(r.scope == "on_net_only" for r in rows))
            self.assertTrue(all(r.availability == "not_checked" for r in rows))
            self.assertFalse(any(r.publicly_routable for r in rows))

    def test_e164_shape_is_not_ownership(self):
        self.assertTrue(e164_syntax("+48501111222"))
        self.assertFalse(e164_syntax("+00123"))
        self.assertFalse(e164_syntax("48501111222"))
        self.assertEqual(digits_only("000 111-222"), "000111222")
        with self.assertRaises(ValueError):
            digits_only("+48501111222")

    def test_unverified_inventory_is_never_approved(self):
        entries = [
            {"e164": "+48501111222", "available": True, "verified_provider": False,
             "provider_reference": "candidate"},
            {"e164": "+48501111223", "available": True, "verified_provider": True,
             "provider_reference": "provider-item-123"},
            {"e164": "+48501111224", "available": False, "verified_provider": True,
             "provider_reference": "provider-item-124"},
        ]
        approved = filter_verified_carrier_inventory(entries)
        self.assertEqual(len(approved), 1)
        self.assertEqual(approved[0]["e164"], "+48501111223")


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_private_capabilities_fail_closed(self):
        with patch("services.ai_studio.omni_orchestrator.API_KEY", "test-gateway-key"):
            self.assertEqual(self.client.get("/api/virtual-number/capabilities").status_code, 401)
            reply = self.client.get("/api/virtual-number/capabilities",
                                    headers={"Authorization": "Bearer test-gateway-key"})
            self.assertEqual(reply.status_code, 200)
            self.assertFalse(reply.json()["public_number_reservation"])
            self.assertFalse(reply.json()["outbound_pstn_enabled"])

    def test_suggestions_return_unroutable_identifiers(self):
        with patch("services.ai_studio.omni_orchestrator.API_KEY", "test-gateway-key"):
            reply = self.client.post("/api/virtual-number/suggest",
                                     json={"prefix": "111", "length": 9, "count": 5},
                                     headers={"Authorization": "Bearer test-gateway-key"})
            self.assertEqual(reply.status_code, 200, reply.text)
            self.assertFalse(reply.json()["carrier_checked"])
            self.assertEqual(len(reply.json()["candidates"]), 5)
            self.assertTrue(all(not x["publicly_routable"] for x in reply.json()["candidates"]))

    def test_invalid_prefix_does_not_reach_telephony(self):
        with patch("services.ai_studio.omni_orchestrator.API_KEY", "test-gateway-key"):
            reply = self.client.post("/api/virtual-number/suggest",
                                     json={"prefix": "+4879", "length": 9},
                                     headers={"Authorization": "Bearer test-gateway-key"})
            self.assertIn(reply.status_code, (400, 422))

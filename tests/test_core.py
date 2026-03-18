"""Tests for Aquawatch."""
from src.core import Aquawatch
def test_init(): assert Aquawatch().get_stats()["ops"] == 0
def test_op(): c = Aquawatch(); c.detect(x=1); assert c.get_stats()["ops"] == 1
def test_multi(): c = Aquawatch(); [c.detect() for _ in range(5)]; assert c.get_stats()["ops"] == 5
def test_reset(): c = Aquawatch(); c.detect(); c.reset(); assert c.get_stats()["ops"] == 0
def test_service_name(): c = Aquawatch(); r = c.detect(); assert r["service"] == "aquawatch"

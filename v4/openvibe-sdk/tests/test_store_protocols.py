import typing

from openvibe_sdk.memory.stores import EpisodicStore, FactStore, InsightStore


def test_fact_store_is_protocol():
    assert issubclass(type(FactStore), type(typing.Protocol))


def test_episodic_store_is_protocol():
    assert issubclass(type(EpisodicStore), type(typing.Protocol))


def test_insight_store_is_protocol():
    assert issubclass(type(InsightStore), type(typing.Protocol))

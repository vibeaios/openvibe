def test_data_ops_role_exists():
    from vibe_inc.roles.data_ops import DataOps
    assert DataOps.role_id == "data_ops"
    assert len(DataOps.operators) == 3


def test_data_ops_has_soul():
    from vibe_inc.roles.data_ops import DataOps
    assert "source of truth" in DataOps.soul.lower()


def test_data_ops_operators():
    from vibe_inc.roles.data_ops import DataOps
    from vibe_inc.roles.data_ops.catalog_ops import CatalogOps
    from vibe_inc.roles.data_ops.quality_ops import QualityOps
    from vibe_inc.roles.data_ops.access_ops import AccessOps
    assert CatalogOps in DataOps.operators
    assert QualityOps in DataOps.operators
    assert AccessOps in DataOps.operators

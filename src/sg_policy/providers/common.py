from typing import Dict


def create_result_dict(value=None, meta=None, err=None) -> Dict:
    return dict(value=value, meta=meta, err=err)

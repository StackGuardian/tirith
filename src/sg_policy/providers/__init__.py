from typing import Callable, Dict

from .terraform_plan.handler import *
from .infracost import provide as infracost_provider
from .sg_workflow import provide as sg_wf_provider
from .terraform_plan import provide as terraform_provider


PROVIDERS_DICT: Dict[str, Callable] = {
    "stackguardian/terraform_plan": terraform_provider,
    "stackguardian/infracost": infracost_provider,
    "stackguardian/sg_workflow": sg_wf_provider,
}

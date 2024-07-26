from typing import Callable, Dict

from .infracost import provide as infracost_provider
from .json import provide as json_provider
from .kubernetes import provide as kubernetes_provider
from .sg_workflow import provide as sg_wf_provider
from .terraform_plan import provide as terraform_provider
from .terraform_plan.handler import *

PROVIDERS_DICT: Dict[str, Callable] = {
    "stackguardian/terraform_plan": terraform_provider,
    "stackguardian/infracost": infracost_provider,
    "stackguardian/sg_workflow": sg_wf_provider,
    "stackguardian/json": json_provider,
    "stackguardian/kubernetes": kubernetes_provider,
}

from enum import Enum, unique
from utils.constant import BEDROCK_MODEL_IDS


@unique
class ErrorEnum(Enum):
    SUCCEEDED = {1: "Operation succeeded"}
    NOT_SUPPORTED = {1001: "Your query statement is currently not supported by the system"}
    INVAILD_BEDROCK_MODEL_ID = {1002: f"Invalid bedrock model id.Vaild ids:{BEDROCK_MODEL_IDS}"}
    INVAILD_SESSION_ID = {1003: f"Invalid session id."}
    PROFILE_NOT_FOUND = {1004: "Profile name not found."}
    UNKNOWN_ERROR = {9999: "Unknown error."}

    def get_code(self):
        return list(self.value.keys())[0]

    def get_message(self):
        return list(self.value.values())[0]


@unique
class ContentEnum(Enum):
    EXCEPTION = "exception"
    COMMON = "common"
    STATE = "state"
    END = "end"
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class CredentialModel(str, Enum):
    SELF_SERVE = "self_serve"
    MIXED = "mixed"
    GATED = "gated"
    UNKNOWN = "unknown"


class MCPStatus(str, Enum):
    OFFICIAL_FIRST_PARTY = "official_first_party"
    OFFICIAL_HOSTED = "official_hosted"
    OFFICIAL_REMOTE = "official_remote"
    THIRD_PARTY = "third_party"
    COMMUNITY = "community"
    SELF_HOSTED = "self_hosted"
    NONE_FOUND = "none_found"
    UNKNOWN = "unknown"


class Buildability(str, Enum):
    YES = "yes"
    YES_WITH_CONSTRAINTS = "yes_with_constraints"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Evidence(BaseModel):
    claim: str
    url: str
    source_title: Optional[str] = None
    source_type: str
    evidence_note: str
    retrieved_at: str
    supports_claim: Optional[bool] = None
    verification_status: str = "unverified"


class AccessAssessment(BaseModel):
    model: CredentialModel
    details: str
    plan_requirement: Optional[str] = None
    approval_requirement: Optional[str] = None


class APIAssessment(BaseModel):
    types: List[str] = Field(default_factory=list)
    breadth: str = "unknown"
    details: str = ""


class MCPAssessment(BaseModel):
    status: MCPStatus
    details: str = ""


class BuildabilityAssessment(BaseModel):
    verdict: Buildability
    blockers: List[str] = Field(default_factory=list)
    rationale: str = ""


class Confidence(BaseModel):
    overall: ConfidenceLevel
    auth: ConfidenceLevel
    credential_access: ConfidenceLevel
    api: ConfidenceLevel
    mcp: ConfidenceLevel
    buildability: ConfidenceLevel


class Verification(BaseModel):
    status: str = "unverified"
    verifier_agrees: Optional[bool] = None
    human_verified: bool = False
    notes: str = ""


class AppResearchRecord(BaseModel):
    app: str
    domain: str
    category: str

    description: str

    auth_methods: List[str] = Field(default_factory=list)

    access: AccessAssessment

    api: APIAssessment

    mcp: MCPAssessment

    buildability: BuildabilityAssessment

    evidence: List[Evidence] = Field(default_factory=list)

    confidence: Confidence

    verification: Verification

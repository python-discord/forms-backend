from pydantic import BaseModel


class AntiSpam(BaseModel):
    """Schema model for form response antispam field."""

    ip_hash: str
    user_agent_hash: str
    captcha_pass: bool
    dns_blacklisted: bool

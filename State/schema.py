from typing import TypedDict, List, Optional, Dict, Any

class CampaignState(TypedDict):
    # ── INTAKE (filled by user via intake agent) ──
    business_name: str
    business_address: str
    project_name: str
    user_email: str
    services: List[str]
    service_areas: List[str]
    target_customer: str
    unique_value_props: List[str]
    page_urls: List[Dict]
    competitors: List[str]
    monthly_budget: str
    campaign_goal: str
    portfolio_images: List[str]

    # ── STRATEGY OUTPUTS ──
    seo_report: Optional[Dict]
    google_ads_plan: Optional[Dict]
    meta_ads_plan: Optional[Dict]

    # ── CREATIVE OUTPUTS ──
    ad_copy: Optional[Dict]
    visual_concepts: Optional[Dict]

    # ── HUMAN REVIEW DECISIONS ──
    strategy_approved: bool
    strategy_feedback: Optional[str]
    creative_approved: bool
    creative_feedback: Optional[str]
    final_approved: bool

    # ── DELIVERY ──
    drive_folder_id: Optional[str]
    drive_folder_url: Optional[str]
    uploaded_files: List[str]
    email_sent: bool

    # ── MEMORY ──
    similar_past_campaigns: Optional[List[str]]

    # ── FLOW CONTROL ──
    current_step: str
    errors: List[str]
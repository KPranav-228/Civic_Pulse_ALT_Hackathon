"""Personalization Engine for CivicPulse Alerts.

Adapts "What You Should Do" checklist and advisory actions based on citizen profile:
- Water Source: municipal tap, private/govt tanker, borewell, or mixed
- Housing Type: apartment society, independent bungalow, or gated villa
- Vulnerable Modes: dialysis patient, medical oxygen, elderly living alone, work-from-home (WFH)
"""

from typing import Any, Dict, List, Optional, Tuple


def tailor_actions_for_profile(
    base_actions: List[str],
    category: str,
    water_source: str = "municipal",
    housing_type: str = "apartment",
    vulnerable_modes: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Tailor alert action checklists according to citizen household characteristics.

    Returns:
        dict containing:
        - "actions": list of tailored action checklist strings
        - "custom_notes": list of profile-specific advisory notices
        - "tailored_tags": list of tag badges applied (e.g. ["Apartment", "Tanker Reliant", "Elderly Care"])
    """
    actions = list(base_actions or [])
    custom_notes = []
    tailored_tags = []
    vulnerable_modes = [m.lower() for m in (vulnerable_modes or [])]

    # Normalize profile attributes
    w_source = (water_source or "municipal").lower()
    h_type = (housing_type or "apartment").lower()

    # ---------------------------------------------------------
    # 1. Category: WATER SUPPLY
    # ---------------------------------------------------------
    if category == "water_supply":
        if w_source == "borewell":
            tailored_tags.append("Borewell Setup")
            custom_notes.append("Groundwater reliance: Municipal disruption has low immediate tap impact.")
            actions.insert(0, "Check borewell pump pressure and conserve underground aquifer levels during peak hours.")
        elif w_source == "tanker":
            tailored_tags.append("Tanker Reliant")
            custom_notes.append("High tanker demand expected across private and GHMC/HMWSSB depots.")
            actions.insert(0, "Book municipal or private water tanker immediately (at least 6-8 hours in advance).")
            actions.append("Prioritize water storage strictly for potable use and drinking.")
        else:  # municipal
            tailored_tags.append("Municipal Tap Supply")
            actions.insert(0, "Direct municipal pipeline impact: Fill all domestic sumps and overhead tanks before supply shutdown.")

        if h_type == "apartment":
            tailored_tags.append("Apartment Society")
            actions.append("Notify Apartment Residents Welfare Association (RWA) to ration common overhead water tanks.")
        elif h_type in {"independent", "villa"}:
            tailored_tags.append("Independent House")
            actions.append("Operate ground motor booster early to maximize internal sump reserve before pipeline pressure falls.")

    # ---------------------------------------------------------
    # 2. Category: POWER CUT
    # ---------------------------------------------------------
    elif category == "power_cut":
        if h_type == "apartment":
            tailored_tags.append("Apartment Society")
            actions.append("Verify DG (diesel generator) backup run-schedule with building maintenance for elevators and water pumps.")
        elif h_type in {"independent", "villa"}:
            tailored_tags.append("Inverter Dependent")
            actions.append("Charge home inverter batteries fully and turn off high-load inductive appliances (ACs, geysers, motor pumps).")

        # Vulnerable modes impact on power cuts
        if "dialysis" in vulnerable_modes or "home_oxygen" in vulnerable_modes:
            tailored_tags.append("Critical Medical Support")
            custom_notes.append("CRITICAL: Patient medical equipment backup required.")
            actions.insert(0, "EMERGENCY PREP: Verify medical oxygen / peritoneal dialysis equipment uninterruptible power supply (UPS) or locate nearest operational 24/7 hospital.")
        if "elderly" in vulnerable_modes:
            tailored_tags.append("Elderly Care")
            actions.append("Keep emergency rechargeable lamps and battery-powered fans accessible at ground level for seniors.")
        if "wfh" in vulnerable_modes:
            tailored_tags.append("WFH Continuity")
            actions.append("Ensure secondary mobile hotspot / mini-UPS for Wi-Fi router is fully charged for uninterrupted work.")

    # ---------------------------------------------------------
    # 3. Category: SEVERE WEATHER / FLOODING
    # ---------------------------------------------------------
    elif category == "severe_weather":
        if h_type == "apartment":
            tailored_tags.append("Basement Parking Alert")
            actions.insert(0, "Move vehicles from cellar/basement parking to elevated ramps to prevent flash-inundation damage.")
        elif h_type in {"independent", "villa"}:
            tailored_tags.append("Ground Level House")
            actions.append("Inspect ground drains, clear perimeter leaf grates, and ensure sandbags or barriers are ready near ground entries.")

        if "elderly" in vulnerable_modes:
            tailored_tags.append("Senior Safety")
            actions.append("Ensure essential prescriptions and medications are stocked for 48 hours without needing to venture outside.")

    # ---------------------------------------------------------
    # 4. Category: ROAD CLOSURE
    # ---------------------------------------------------------
    elif category == "road_closure":
        if "wfh" in vulnerable_modes:
            tailored_tags.append("WFH Advisory")
            actions.insert(0, "Opt to Work-From-Home if commuting through this sector during scheduled closure hours.")

    # Deduplicate actions while preserving order
    deduped_actions = []
    seen = set()
    for act in actions:
        if act not in seen:
            seen.add(act)
            deduped_actions.append(act)

    return {
        "actions": deduped_actions,
        "custom_notes": custom_notes,
        "tailored_tags": tailored_tags,
        "water_source": w_source,
        "housing_type": h_type,
        "vulnerable_modes": vulnerable_modes
    }


def compute_effective_severity(
    base_severity: str,
    category: str,
    vulnerable_modes: Optional[List[str]] = None
) -> Tuple[str, Optional[str]]:
    """Elevate effective severity for vulnerable citizens during critical disruptions.

    Returns:
        (effective_severity, reason_or_none)
    """
    v_modes = [m.lower() for m in (vulnerable_modes or [])]
    base = base_severity.lower()

    if category == "power_cut":
        if "dialysis" in v_modes or "home_oxygen" in v_modes:
            if base != "critical":
                return "critical", "Elevated to Critical: Household relies on continuous medical life support equipment."
        elif "elderly" in v_modes and base in {"info", "advisory"}:
            return "warning", "Elevated to Warning: Elderly resident living alone during scheduled power outage."
        elif "wfh" in v_modes and base == "info":
            return "advisory", "Elevated to Advisory: Work-from-home electrical continuity advisory."

    elif category == "severe_weather":
        if ("dialysis" in v_modes or "home_oxygen" in v_modes or "elderly" in v_modes) and base in {"info", "advisory"}:
            return "warning", "Elevated to Warning: Mobility or medical vulnerability during severe weather."

    return base, None


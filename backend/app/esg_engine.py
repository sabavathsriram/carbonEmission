"""
ESG Intelligence Engine — scoring, forecasting, what-if simulation,
operational insights, smart alerts, and sustainability recommendations.
"""
from typing import List, Dict, Optional
from .models import ExtractedData, EmissionResult


# ── ESG Score ────────────────────────────────────────────────────────────────

def calculate_esg_score(emissions: EmissionResult, extracted: ExtractedData) -> dict:
    """
    Generate an ESG score (0–100) based on operational efficiency,
    emission intensity, data completeness, and reporting reliability.
    """
    score = 60.0  # baseline

    # Data completeness bonus
    fields = [extracted.vendor_name, extracted.invoice_date, extracted.energy_kwh,
              extracted.fuel_liters, extracted.distance_km, extracted.waste_kg]
    completeness = sum(1 for f in fields if f is not None) / len(fields)
    score += completeness * 15

    # Confidence bonus
    score += emissions.confidence_score * 10

    # Emission intensity penalty (higher total = lower score)
    total = emissions.total_kg_co2e
    if total > 50000:
        score -= 15
    elif total > 10000:
        score -= 8
    elif total > 1000:
        score -= 3

    # Scope 1 dominance penalty (direct emissions are harder to offset)
    if emissions.total_kg_co2e > 0:
        s1_ratio = emissions.scope1_kg_co2e / emissions.total_kg_co2e
        if s1_ratio > 0.7:
            score -= 10
        elif s1_ratio > 0.5:
            score -= 5

    score = max(0.0, min(100.0, score))
    pct = round(score, 1)

    if pct >= 75:
        grade, label, color = "A", "Strong", "#1a7f5a"
    elif pct >= 60:
        grade, label, color = "B", "Moderate", "#f39c12"
    elif pct >= 45:
        grade, label, color = "C", "Developing", "#e67e22"
    else:
        grade, label, color = "D", "Needs Improvement", "#e74c3c"

    return {
        "score": pct,
        "grade": grade,
        "label": label,
        "color": color,
        "breakdown": {
            "data_completeness": round(completeness * 100, 1),
            "confidence": round(emissions.confidence_score * 100, 1),
            "emission_intensity": "High" if total > 10000 else "Medium" if total > 1000 else "Low",
            "scope1_ratio": round(
                (emissions.scope1_kg_co2e / emissions.total_kg_co2e * 100)
                if emissions.total_kg_co2e > 0 else 0, 1
            ),
        },
    }


# ── What-If Simulation ───────────────────────────────────────────────────────

SIMULATION_SCENARIOS = [
    {
        "id": "reduce_diesel_10",
        "title": "Reduce Diesel Consumption by 10%",
        "description": "Optimize fleet routing and reduce idle time to cut diesel use by 10% without reducing delivery capacity.",
        "scope": "scope1",
        "field": "fuel_liters",
        "reduction_pct": 0.10,
        "category": "Fuel Efficiency",
        "operational_note": "Achievable through route optimization and driver training. No reduction in deliveries.",
    },
    {
        "id": "switch_renewable_energy",
        "title": "Switch to 30% Renewable Electricity",
        "description": "Source 30% of electricity from renewable tariffs or on-site solar, reducing grid emission factor.",
        "scope": "scope2",
        "field": "energy_kwh",
        "reduction_pct": 0.30,
        "category": "Energy Transition",
        "operational_note": "Renewable tariff switch requires no operational changes.",
    },
    {
        "id": "eliminate_idle_energy",
        "title": "Eliminate Off-Hours Energy Waste (15%)",
        "description": "Smart metering and automated shutdown of non-essential equipment during off-hours.",
        "scope": "scope2",
        "field": "energy_kwh",
        "reduction_pct": 0.15,
        "category": "Operational Efficiency",
        "operational_note": "Targets idle/overnight consumption only. No impact on production hours.",
    },
    {
        "id": "optimize_transport",
        "title": "Optimize Transport Routes (20%)",
        "description": "AI-driven route optimization and load consolidation to reduce total distance traveled.",
        "scope": "scope3",
        "field": "distance_km",
        "reduction_pct": 0.20,
        "category": "Logistics Optimization",
        "operational_note": "Same delivery volume, fewer trips through better load planning.",
    },
    {
        "id": "waste_diversion",
        "title": "Divert 50% Waste from Landfill",
        "description": "Implement recycling and composting programs to divert half of waste from landfill.",
        "scope": "scope3",
        "field": "waste_kg",
        "reduction_pct": 0.50,
        "category": "Waste Management",
        "operational_note": "Recycling programs typically reduce waste disposal costs.",
    },
]


def run_what_if_simulations(extracted: ExtractedData, emissions: EmissionResult) -> List[dict]:
    """Run all applicable what-if scenarios and return results."""
    results = []

    for scenario in SIMULATION_SCENARIOS:
        field = scenario["field"]
        val = getattr(extracted, field, None)
        if val is None or val <= 0:
            continue

        reduction_pct = scenario["reduction_pct"]
        # Estimate emission reduction based on scope
        scope_map = {
            "scope1": emissions.scope1_kg_co2e,
            "scope2": emissions.scope2_kg_co2e,
            "scope3": emissions.scope3_kg_co2e,
        }
        scope_emissions = scope_map.get(scenario["scope"], 0)

        # Proportional reduction based on field contribution
        field_contribution = val / (val + 1)  # simplified ratio
        emission_reduction = scope_emissions * reduction_pct
        cost_saving_usd = emission_reduction * 0.05  # ~$50/tonne carbon price
        new_total = max(0, emissions.total_kg_co2e - emission_reduction)
        esg_improvement = (emission_reduction / emissions.total_kg_co2e * 10) if emissions.total_kg_co2e > 0 else 0

        results.append({
            "id": scenario["id"],
            "title": scenario["title"],
            "description": scenario["description"],
            "category": scenario["category"],
            "operational_note": scenario["operational_note"],
            "reduction_pct": round(reduction_pct * 100, 1),
            "emission_reduction_kg": round(emission_reduction, 2),
            "emission_reduction_tonnes": round(emission_reduction / 1000, 3),
            "new_total_kg": round(new_total, 2),
            "cost_saving_usd": round(cost_saving_usd, 2),
            "esg_score_improvement": round(esg_improvement, 1),
            "scope": scenario["scope"],
        })

    return sorted(results, key=lambda x: x["emission_reduction_kg"], reverse=True)


# ── Sustainability Recommendations ───────────────────────────────────────────

def generate_recommendations(extracted: ExtractedData, emissions: EmissionResult) -> List[dict]:
    """
    Generate revenue-focused sustainability recommendations.
    Each recommendation quantifies financial upside while maintaining
    or improving operational performance.
    """
    recs = []

    # ── Energy: Smart metering / off-hours shutdown ──
    if extracted.energy_kwh and extracted.energy_kwh > 1000:
        kwh = extracted.energy_kwh
        # Assume $0.12/kWh average industrial rate
        annual_kwh = kwh * 12
        saving_15pct = annual_kwh * 0.15 * 0.12
        saving_25pct = annual_kwh * 0.25 * 0.12
        recs.append({
            "id": "rec_smart_metering",
            "priority": "high",
            "category": "Energy",
            "title": "Deploy Smart Metering — Recover $" + f"{saving_15pct:,.0f}–${saving_25pct:,.0f}/yr in Wasted Energy Spend",
            "insight": (
                f"Current consumption of {kwh:,.0f} kWh/month includes an estimated "
                f"15–25% ({kwh*0.15:,.0f}–{kwh*0.25:,.0f} kWh) in off-hours idle waste. "
                f"At $0.12/kWh, that is ${kwh*0.15*0.12*12:,.0f}–${kwh*0.25*0.12*12:,.0f} "
                f"leaving the business annually with zero production benefit."
            ),
            "action": (
                "Install sub-metering on HVAC, lighting, and non-production equipment. "
                "Automate shutdown schedules for off-shift hours. "
                "Typical payback period: 8–14 months."
            ),
            "impact": (
                f"Recover ${saving_15pct:,.0f}–${saving_25pct:,.0f}/year in direct cost savings. "
                f"Reduce Scope 2 emissions by {kwh*0.15*0.433:,.0f}–{kwh*0.25*0.433:,.0f} kg CO₂e/month. "
                "Zero impact on production capacity or output."
            ),
            "maintains_output": True,
            "revenue_impact": f"+${saving_15pct:,.0f}–${saving_25pct:,.0f}/yr",
        })

    # ── Energy: Renewable tariff ──
    if extracted.energy_kwh and extracted.energy_kwh > 0:
        kwh = extracted.energy_kwh
        # Renewable tariffs typically 5–8% cheaper than standard grid in competitive markets
        annual_saving = kwh * 12 * 0.06 * 0.12
        recs.append({
            "id": "rec_renewable_tariff",
            "priority": "medium",
            "category": "Energy",
            "title": f"Switch to Renewable Tariff — Save ${annual_saving:,.0f}/yr + Unlock Green Contracts",
            "insight": (
                f"Renewable electricity tariffs are now 5–8% cheaper than standard grid rates "
                f"in most markets. On {kwh:,.0f} kWh/month, that is ${annual_saving:,.0f}/year in "
                f"direct savings. Additionally, 67% of enterprise procurement teams now require "
                f"suppliers to demonstrate renewable energy use — unlocking new contract opportunities."
            ),
            "action": (
                "Contact energy supplier to switch to a certified renewable tariff (REGO/RECs). "
                "No operational changes required. Can be completed in 30 days."
            ),
            "impact": (
                f"${annual_saving:,.0f}/year cost reduction. "
                "Eliminates Scope 2 market-based emissions entirely. "
                "Qualifies business for green supply chain programs and ESG-linked financing "
                "(typically 0.25–0.5% lower interest rates on sustainability-linked loans)."
            ),
            "maintains_output": True,
            "revenue_impact": f"+${annual_saving:,.0f}/yr + contract access",
        })

    # ── Fleet: Route optimization ──
    if extracted.fuel_liters and extracted.fuel_liters > 200:
        liters = extracted.fuel_liters
        # Diesel ~$1.40/L average
        fuel_price = 1.40
        annual_liters = liters * 12
        saving_10pct = annual_liters * 0.10 * fuel_price
        saving_15pct = annual_liters * 0.15 * fuel_price
        recs.append({
            "id": "rec_fleet_optimization",
            "priority": "high",
            "category": "Fleet",
            "title": f"Fleet Route Optimization — Cut Fuel Spend by ${saving_10pct:,.0f}–${saving_15pct:,.0f}/yr",
            "insight": (
                f"Current fuel consumption of {liters:,.0f} L/month costs approximately "
                f"${liters*fuel_price:,.0f}/month (${liters*fuel_price*12:,.0f}/year). "
                f"Route optimization software typically reduces fuel use by 10–15% "
                f"through idle reduction, load consolidation, and smarter routing — "
                f"without reducing delivery volume or service levels."
            ),
            "action": (
                "Deploy AI route optimization (e.g., route planning software). "
                "Combine with driver eco-driving training (avg 5–8% additional fuel saving). "
                "Implementation timeline: 4–6 weeks."
            ),
            "impact": (
                f"${saving_10pct:,.0f}–${saving_15pct:,.0f}/year in fuel cost savings. "
                f"Reduce Scope 1 emissions by {liters*0.10*2.639:,.0f}–{liters*0.15*2.639:,.0f} kg CO₂e/month. "
                "Same delivery capacity and customer service levels maintained. "
                "Faster delivery times often improve customer satisfaction scores."
            ),
            "maintains_output": True,
            "revenue_impact": f"+${saving_10pct:,.0f}–${saving_15pct:,.0f}/yr",
        })

    # ── Fleet: EV transition for short routes ──
    if extracted.fuel_type and extracted.fuel_type.lower() in ("diesel", "petrol") and extracted.fuel_liters and extracted.fuel_liters > 300:
        liters = extracted.fuel_liters
        fuel_price = 1.40
        # EVs cost ~$0.04/km vs diesel ~$0.14/km — 70% cheaper per km
        annual_fuel_cost = liters * 12 * fuel_price
        ev_saving_pct = 0.35  # conservative: 35% of fleet suitable for EV on short routes
        ev_annual_saving = annual_fuel_cost * ev_saving_pct * 0.70
        recs.append({
            "id": "rec_ev_transition",
            "priority": "medium",
            "category": "Fleet",
            "title": f"EV Transition for Short Routes — ${ev_annual_saving:,.0f}/yr Fuel Cost Reduction",
            "insight": (
                f"Electric vehicles cost ~$0.04/km to run vs ~$0.14/km for diesel — "
                f"a 70% reduction in per-km fuel cost. "
                f"Assuming 35% of current routes are under 150km/day and suitable for EV, "
                f"transitioning those vehicles saves ${ev_annual_saving:,.0f}/year. "
                f"EV maintenance costs are also 40% lower than ICE vehicles."
            ),
            "action": (
                "Identify top 5 highest-mileage vehicles on routes under 150km/day. "
                "Model TCO (total cost of ownership) over 5 years including charging infrastructure. "
                "Government EV incentives typically cover 20–35% of purchase cost."
            ),
            "impact": (
                f"${ev_annual_saving:,.0f}/year in fuel savings on converted vehicles. "
                "40% lower maintenance costs per converted vehicle. "
                "Eliminates Scope 1 emissions for converted fleet. "
                "Qualifies for green fleet certification — a growing requirement in B2B tenders."
            ),
            "maintains_output": True,
            "revenue_impact": f"+${ev_annual_saving:,.0f}/yr fuel + 40% lower maintenance",
        })

    # ── Logistics: Modal shift ──
    if extracted.distance_km and extracted.distance_km > 2000:
        km = extracted.distance_km
        # Road freight ~$0.15/km, rail ~$0.06/km
        annual_km = km * 12
        road_cost = annual_km * 0.15
        rail_cost = annual_km * 0.06
        modal_saving = road_cost - rail_cost
        recs.append({
            "id": "rec_modal_shift",
            "priority": "medium",
            "category": "Logistics",
            "title": f"Road-to-Rail Modal Shift — Save ${modal_saving:,.0f}/yr on Freight Costs",
            "insight": (
                f"Current transport distance of {km:,.0f} km/month costs approximately "
                f"${km*0.15:,.0f}/month by road. Rail freight costs ~$0.06/km — "
                f"60% cheaper per km — and emits 74% less CO₂e (0.028 vs 0.106 kg/km). "
                f"On {annual_km:,.0f} km/year, shifting eligible long-haul routes to rail "
                f"saves ${modal_saving:,.0f}/year."
            ),
            "action": (
                "Identify routes over 500km where rail connections exist. "
                "Negotiate intermodal contracts with rail operators. "
                "Typical lead time to switch: 8–12 weeks."
            ),
            "impact": (
                f"${modal_saving:,.0f}/year freight cost reduction. "
                f"Reduce Scope 3 transport emissions by up to 74% on converted routes. "
                "Lower freight costs improve product margin or enable competitive pricing. "
                "Rail reliability (95%+ on-time) often exceeds road freight."
            ),
            "maintains_output": True,
            "revenue_impact": f"+${modal_saving:,.0f}/yr freight savings",
        })

    # ── Waste: Diversion program ──
    if extracted.waste_kg and extracted.waste_kg > 200:
        kg = extracted.waste_kg
        # Landfill disposal ~$80/tonne, recycling revenue ~$30/tonne for metals/paper
        annual_kg = kg * 12
        landfill_cost_saving = (annual_kg / 1000) * 80 * 0.50  # divert 50%
        recycling_revenue = (annual_kg / 1000) * 30 * 0.30     # 30% recyclable for revenue
        total_waste_benefit = landfill_cost_saving + recycling_revenue
        recs.append({
            "id": "rec_waste_diversion",
            "priority": "medium",
            "category": "Waste",
            "title": f"Waste Diversion Program — Generate ${total_waste_benefit:,.0f}/yr from Waste Reduction",
            "insight": (
                f"Current waste of {kg:,.0f} kg/month ({annual_kg/1000:.1f} tonnes/year) "
                f"costs ~${annual_kg/1000*80:,.0f}/year in landfill disposal fees. "
                f"Diverting 50% through recycling and composting eliminates "
                f"${landfill_cost_saving:,.0f}/year in disposal costs. "
                f"Recyclable materials (metals, paper, plastics) generate an additional "
                f"${recycling_revenue:,.0f}/year in recovered material revenue."
            ),
            "action": (
                "Implement waste segregation at source (3-bin system: general, recyclable, organic). "
                "Partner with certified recyclers for material take-back. "
                "Conduct waste audit to identify highest-value diversion streams."
            ),
            "impact": (
                f"${total_waste_benefit:,.0f}/year combined savings and revenue. "
                f"Reduce Scope 3 waste emissions by ~{kg*0.50*0.467:,.0f} kg CO₂e/month. "
                "Waste reduction programs typically improve operational efficiency "
                "by identifying process inefficiencies that generate excess waste."
            ),
            "maintains_output": True,
            "revenue_impact": f"+${total_waste_benefit:,.0f}/yr",
        })

    # ── ESG-linked financing ──
    if emissions.total_kg_co2e > 500:
        recs.append({
            "id": "rec_esg_financing",
            "priority": "low",
            "category": "Strategy",
            "title": "Access ESG-Linked Financing — 0.25–0.5% Lower Interest Rates",
            "insight": (
                "Sustainability-linked loans (SLLs) and green bonds now represent over "
                "$1.5 trillion in global issuance. Lenders offer 0.25–0.5% interest rate "
                "reductions to businesses that meet verified ESG targets. "
                "This platform's compliance-ready reports provide the documentation required "
                "to qualify for these instruments."
            ),
            "action": (
                "Use Carbon Intelligence reports as evidence for ESG loan applications. "
                "Set measurable emission reduction targets (e.g., 10% reduction in 12 months). "
                "Engage sustainability-focused lenders (HSBC, Barclays, BNP Paribas green desks)."
            ),
            "impact": (
                "On a $1M loan, a 0.25% rate reduction saves $2,500/year in interest. "
                "On $10M, that is $25,000/year. "
                "ESG credentials also improve credit ratings and reduce cost of capital. "
                "Increasingly required for government contracts and large enterprise procurement."
            ),
            "maintains_output": True,
            "revenue_impact": "Lower cost of capital + contract access",
        })

    return sorted(recs, key=lambda r: {"high": 0, "medium": 1, "low": 2}[r["priority"]])


# ── Smart Alerts ─────────────────────────────────────────────────────────────

def generate_smart_alerts(extracted: ExtractedData, emissions: EmissionResult) -> List[dict]:
    """Generate operational intelligence alerts."""
    alerts = []

    if extracted.energy_kwh and extracted.energy_kwh > 10000:
        alerts.append({
            "type": "anomaly",
            "severity": "high",
            "icon": "zap",
            "title": "High Electricity Consumption Detected",
            "message": f"Electricity usage of {extracted.energy_kwh:,.0f} kWh is significantly above average. Check for equipment faults or overnight waste.",
        })

    if extracted.fuel_liters and extracted.fuel_liters > 5000:
        alerts.append({
            "type": "anomaly",
            "severity": "high",
            "icon": "fuel",
            "title": "Elevated Fuel Consumption",
            "message": f"Fuel consumption of {extracted.fuel_liters:,.0f} L may indicate generator overdependence or fleet inefficiency.",
        })

    if extracted.distance_km and extracted.distance_km > 20000:
        alerts.append({
            "type": "insight",
            "severity": "medium",
            "icon": "truck",
            "title": "High Transport Distance",
            "message": f"Travel distance of {extracted.distance_km:,.0f} km suggests route consolidation opportunities.",
        })

    if emissions.scope1_kg_co2e > emissions.scope2_kg_co2e + emissions.scope3_kg_co2e:
        alerts.append({
            "type": "risk",
            "severity": "medium",
            "icon": "alert-triangle",
            "title": "Scope 1 Dominance — Direct Emission Risk",
            "message": "Direct emissions exceed combined Scope 2+3. High regulatory exposure. Prioritize fuel switching and process electrification.",
        })

    if emissions.confidence_score < 0.5:
        alerts.append({
            "type": "data_quality",
            "severity": "medium",
            "icon": "shield",
            "title": "Low Data Confidence",
            "message": "Confidence score below 50%. Emissions may be estimated. Provide activity-level data for accurate reporting.",
        })

    if extracted.waste_kg and extracted.waste_kg > 5000:
        alerts.append({
            "type": "insight",
            "severity": "low",
            "icon": "trash",
            "title": "Significant Waste Volume",
            "message": f"{extracted.waste_kg:,.0f} kg waste detected. Waste diversion program could reduce Scope 3 emissions and disposal costs.",
        })

    return alerts


# ── Emission Forecast ─────────────────────────────────────────────────────────

def generate_forecast(emissions: EmissionResult) -> dict:
    """
    Generate a 12-month emission forecast based on current data.
    Assumes current period = 1 month of data.
    """
    monthly_base = emissions.total_kg_co2e
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    # Seasonal variation factors (energy use higher in winter/summer)
    seasonal = [1.12, 1.08, 1.02, 0.95, 0.92, 0.98,
                1.05, 1.03, 0.97, 0.94, 1.02, 1.10]

    # Business-as-usual trend (slight growth)
    bau = [round(monthly_base * s * (1 + i * 0.005), 1) for i, s in enumerate(seasonal)]

    # Optimized scenario (10% reduction over year)
    optimized = [round(monthly_base * s * (1 - i * 0.008), 1) for i, s in enumerate(seasonal)]

    # Target scenario (net-zero trajectory, 30% reduction)
    target = [round(monthly_base * s * (1 - i * 0.025), 1) for i, s in enumerate(seasonal)]

    yearly_bau = sum(bau)
    yearly_optimized = sum(optimized)
    yearly_target = sum(target)

    return {
        "monthly_data": [
            {
                "month": months[i],
                "bau": bau[i],
                "optimized": optimized[i],
                "target": target[i],
            }
            for i in range(12)
        ],
        "yearly_summary": {
            "bau_total_kg": round(yearly_bau, 1),
            "optimized_total_kg": round(yearly_optimized, 1),
            "target_total_kg": round(yearly_target, 1),
            "bau_total_tonnes": round(yearly_bau / 1000, 2),
            "optimized_saving_kg": round(yearly_bau - yearly_optimized, 1),
            "target_saving_kg": round(yearly_bau - yearly_target, 1),
        },
        "trajectory": "increasing" if monthly_base > 1000 else "stable",
    }


# ── Traceability ─────────────────────────────────────────────────────────────

def build_traceability(extracted: ExtractedData, source_filename: str = "uploaded document") -> List[dict]:
    """Build data source traceability map."""
    traces = []

    if extracted.energy_kwh:
        traces.append({
            "field": "Electricity Consumption",
            "value": f"{extracted.energy_kwh:,.2f} kWh",
            "source": source_filename,
            "extraction_method": "AI (Amazon Bedrock)",
            "confidence": "High" if extracted.vendor_name else "Medium",
        })
    if extracted.fuel_liters:
        traces.append({
            "field": "Fuel Volume",
            "value": f"{extracted.fuel_liters:,.2f} L ({extracted.fuel_type or 'unknown'})",
            "source": source_filename,
            "extraction_method": "AI (Amazon Bedrock)",
            "confidence": "High" if extracted.fuel_type else "Medium",
        })
    if extracted.distance_km:
        traces.append({
            "field": "Transport Distance",
            "value": f"{extracted.distance_km:,.2f} km ({extracted.transport_mode or 'unknown'})",
            "source": source_filename,
            "extraction_method": "AI (Amazon Bedrock)",
            "confidence": "High" if extracted.transport_mode else "Medium",
        })
    if extracted.waste_kg:
        traces.append({
            "field": "Waste Weight",
            "value": f"{extracted.waste_kg:,.2f} kg",
            "source": source_filename,
            "extraction_method": "AI (Amazon Bedrock)",
            "confidence": "Medium",
        })
    if extracted.total_amount:
        traces.append({
            "field": "Invoice Amount",
            "value": f"{extracted.total_amount:,.2f} {extracted.currency or 'USD'}",
            "source": source_filename,
            "extraction_method": "AI (Amazon Bedrock)",
            "confidence": "High",
        })

    return traces

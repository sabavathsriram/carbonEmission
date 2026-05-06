"""
Emissions calculator using standard emission factors.
Sources: IPCC, EPA, DEFRA emission factor databases.
"""
from .models import ExtractedData, EmissionResult

# Emission factors (kg CO2e per unit)
EMISSION_FACTORS = {
    # Electricity (Scope 2) - global average grid
    "electricity_kwh": 0.4330,  # kg CO2e per kWh (IEA global average 2023)

    # Fuels (Scope 1) - kg CO2e per liter
    "diesel": 2.6391,
    "petrol": 2.3122,
    "natural_gas_liter": 1.8897,  # per liter equivalent
    "lpg": 1.5551,

    # Transport (Scope 3) - kg CO2e per km
    "road_freight_km": 0.1062,   # per tonne-km, using 1 tonne default
    "air_freight_km": 0.6020,
    "rail_freight_km": 0.0280,
    "sea_freight_km": 0.0160,

    # Waste (Scope 3) - kg CO2e per kg waste
    "waste_landfill": 0.4670,
    "waste_recycled": 0.0210,
}

FUEL_TYPE_MAP = {
    "diesel": "diesel",
    "petrol": "petrol",
    "gasoline": "petrol",
    "natural_gas": "natural_gas_liter",
    "gas": "natural_gas_liter",
    "lpg": "lpg",
    "lng": "natural_gas_liter",
}

TRANSPORT_MODE_MAP = {
    "road": "road_freight_km",
    "truck": "road_freight_km",
    "air": "air_freight_km",
    "plane": "air_freight_km",
    "rail": "rail_freight_km",
    "train": "rail_freight_km",
    "sea": "sea_freight_km",
    "ship": "sea_freight_km",
    "ocean": "sea_freight_km",
}


def calculate_emissions(data: ExtractedData, confidence_score: float) -> EmissionResult:
    """Calculate GHG emissions from extracted invoice data."""
    scope1 = 0.0
    scope2 = 0.0
    scope3 = 0.0
    breakdown = []

    # --- Scope 2: Electricity ---
    if data.energy_kwh and data.energy_kwh > 0:
        kwh_emissions = data.energy_kwh * EMISSION_FACTORS["electricity_kwh"]
        scope2 += kwh_emissions
        breakdown.append({
            "category": "Scope 2 - Electricity",
            "quantity": data.energy_kwh,
            "unit": "kWh",
            "emission_factor": EMISSION_FACTORS["electricity_kwh"],
            "kg_co2e": round(kwh_emissions, 3),
        })

    # --- Scope 1: Fuel combustion ---
    if data.fuel_liters and data.fuel_liters > 0:
        fuel_key = "diesel"  # default
        if data.fuel_type:
            normalized = data.fuel_type.lower().strip()
            fuel_key = FUEL_TYPE_MAP.get(normalized, "diesel")

        factor = EMISSION_FACTORS.get(fuel_key, EMISSION_FACTORS["diesel"])
        fuel_emissions = data.fuel_liters * factor
        scope1 += fuel_emissions
        breakdown.append({
            "category": "Scope 1 - Fuel Combustion",
            "quantity": data.fuel_liters,
            "unit": "liters",
            "fuel_type": data.fuel_type or "diesel",
            "emission_factor": factor,
            "kg_co2e": round(fuel_emissions, 3),
        })

    # --- Scope 3: Transport / freight ---
    if data.distance_km and data.distance_km > 0:
        mode_key = "road_freight_km"  # default
        if data.transport_mode:
            normalized = data.transport_mode.lower().strip()
            mode_key = TRANSPORT_MODE_MAP.get(normalized, "road_freight_km")

        factor = EMISSION_FACTORS.get(mode_key, EMISSION_FACTORS["road_freight_km"])
        transport_emissions = data.distance_km * factor
        scope3 += transport_emissions
        breakdown.append({
            "category": "Scope 3 - Transport",
            "quantity": data.distance_km,
            "unit": "km",
            "transport_mode": data.transport_mode or "road",
            "emission_factor": factor,
            "kg_co2e": round(transport_emissions, 3),
        })

    # --- Scope 3: Waste ---
    if data.waste_kg and data.waste_kg > 0:
        waste_emissions = data.waste_kg * EMISSION_FACTORS["waste_landfill"]
        scope3 += waste_emissions
        breakdown.append({
            "category": "Scope 3 - Waste",
            "quantity": data.waste_kg,
            "unit": "kg",
            "emission_factor": EMISSION_FACTORS["waste_landfill"],
            "kg_co2e": round(waste_emissions, 3),
        })

    # --- Fallback: estimate from invoice amount if no direct data ---
    if scope1 == 0 and scope2 == 0 and scope3 == 0 and data.total_amount:
        # Very rough spend-based estimate: ~0.3 kg CO2e per USD spent (services average)
        estimated = data.total_amount * 0.3
        scope3 += estimated
        breakdown.append({
            "category": "Scope 3 - Spend-Based Estimate",
            "quantity": data.total_amount,
            "unit": data.currency or "USD",
            "emission_factor": 0.3,
            "kg_co2e": round(estimated, 3),
            "note": "Estimated from invoice value. Provide activity data for accuracy.",
        })
        confidence_score = min(confidence_score, 0.4)

    total = scope1 + scope2 + scope3

    notes = (
        "Emissions calculated using IPCC/EPA/DEFRA emission factors. "
        "Scope 1: direct combustion. Scope 2: purchased electricity. "
        "Scope 3: upstream/downstream activities."
    )

    return EmissionResult(
        scope1_kg_co2e=round(scope1, 3),
        scope2_kg_co2e=round(scope2, 3),
        scope3_kg_co2e=round(scope3, 3),
        total_kg_co2e=round(total, 3),
        breakdown=breakdown,
        confidence_score=round(confidence_score, 2),
        methodology_notes=notes,
    )

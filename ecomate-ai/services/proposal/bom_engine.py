from typing import List, Dict, Optional, Any
from .models import Component, BOMItem, BillOfMaterials, ProjectRequirements, ComponentType, SystemSpec
import json
import logging
from datetime import datetime
import asyncio
from ..vendors.client import VendorClient
from ..vendors.models import VendorCredentials

logger = logging.getLogger(__name__)

class ComponentDatabase:
    """Component database for storing and retrieving components"""
    
    def __init__(self):
        self.components: Dict[str, Component] = {}
        self._load_default_components()
    
    def _load_default_components(self):
        """Load default components into the database"""
        default_components = [
            Component(
                id="pump_001",
                name="Centrifugal Pump 100 GPM",
                type=ComponentType.PUMP,
                manufacturer="Grundfos",
                model="CR32-4",
                specifications={"flow_rate_gpm": 100, "head_ft": 150, "efficiency": 0.85},
                unit_cost=2500.0,
                installation_cost=500.0,
                maintenance_cost_annual=200.0,
                lifespan_years=15,
                energy_consumption_kwh=5.5
            ),
            Component(
                id="blower_001",
                name="Rotary Lobe Blower 500 CFM",
                type=ComponentType.BLOWER,
                manufacturer="Gardner Denver",
                model="YCGA-500",
                specifications={"flow_rate_cfm": 500, "pressure_psi": 15},
                unit_cost=8500.0,
                installation_cost=1200.0,
                maintenance_cost_annual=800.0,
                lifespan_years=12,
                energy_consumption_kwh=15.0
            ),
            Component(
                id="tank_001",
                name="Clarifier Tank 50000 Gal",
                type=ComponentType.TANK,
                manufacturer="Enviroquip",
                model="CL-50K",
                specifications={"capacity_gal": 50000, "diameter_ft": 30, "depth_ft": 12},
                unit_cost=45000.0,
                installation_cost=8000.0,
                maintenance_cost_annual=1500.0,
                lifespan_years=25
            ),
            Component(
                id="membrane_001",
                name="MBR Membrane Module",
                type=ComponentType.MEMBRANE,
                manufacturer="Kubota",
                model="EK-400",
                specifications={"surface_area_sqft": 4300, "pore_size_micron": 0.4},
                unit_cost=12000.0,
                installation_cost=2000.0,
                maintenance_cost_annual=2400.0,
                lifespan_years=8
            )
        ]
        
        for component in default_components:
            self.components[component.id] = component
    
    def add_component(self, component: Component):
        """Add a component to the database"""
        self.components[component.id] = component
    
    def get_component(self, component_id: str) -> Optional[Component]:
        """Get a component by ID"""
        return self.components.get(component_id)
    
    def search_components(self, 
                         component_type: Optional[ComponentType] = None,
                         manufacturer: Optional[str] = None,
                         specifications: Optional[Dict[str, Any]] = None) -> List[Component]:
        """Search components by criteria"""
        results = []
        
        for component in self.components.values():
            if component_type and component.type != component_type:
                continue
            if manufacturer and component.manufacturer.lower() != manufacturer.lower():
                continue
            if specifications:
                match = True
                for key, value in specifications.items():
                    if key not in component.specifications:
                        match = False
                        break
                    if isinstance(value, (int, float)):
                        if component.specifications[key] < value * 0.8:  # 20% tolerance
                            match = False
                            break
                if not match:
                    continue
            
            results.append(component)
        
        return results

class BOMEngine:
    """Bill of Materials generation engine"""
    
    def __init__(self, component_db: ComponentDatabase):
        self.component_db = component_db
        self.selection_rules = self._load_selection_rules()
    
    def _load_selection_rules(self) -> Dict[str, Any]:
        """Load component selection rules"""
        return {
            "pump_sizing": {
                "safety_factor": 1.2,
                "efficiency_min": 0.75
            },
            "blower_sizing": {
                "safety_factor": 1.15,
                "pressure_margin_psi": 2.0
            },
            "tank_sizing": {
                "detention_time_hours": 4.0,
                "safety_factor": 1.1
            },
            "membrane_sizing": {
                "flux_rate_gfd": 15.0,
                "safety_factor": 1.25
            }
        }
    
    def generate_bom(self, project_id: str, requirements: ProjectRequirements) -> BillOfMaterials:
        """Generate bill of materials based on project requirements"""
        logger.info(f"Generating BOM for project {project_id}")
        
        bom_items = []
        
        # Select pumps based on flow rate
        pumps = self._select_pumps(requirements)
        bom_items.extend(pumps)
        
        # Select blowers for aeration
        if "aeration" in requirements.treatment_type.lower():
            blowers = self._select_blowers(requirements)
            bom_items.extend(blowers)
        
        # Select tanks
        tanks = self._select_tanks(requirements)
        bom_items.extend(tanks)
        
        # Select membranes for MBR systems
        if "mbr" in requirements.treatment_type.lower():
            membranes = self._select_membranes(requirements)
            bom_items.extend(membranes)
        
        # Calculate totals
        total_material_cost = sum(item.component.unit_cost * item.quantity for item in bom_items)
        total_installation_cost = sum(item.component.installation_cost * item.quantity for item in bom_items)
        total_cost = total_material_cost + total_installation_cost
        
        bom = BillOfMaterials(
            id=f"bom_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            project_id=project_id,
            items=bom_items,
            total_material_cost=total_material_cost,
            total_installation_cost=total_installation_cost,
            total_cost=total_cost
        )
        
        logger.info(f"Generated BOM with {len(bom_items)} items, total cost: ${total_cost:,.2f}")
        return bom
    
    def _select_pumps(self, requirements: ProjectRequirements) -> List[BOMItem]:
        """Select appropriate pumps based on flow requirements"""
        flow_gpm = requirements.flow_rate_mgd * 694.4  # Convert MGD to GPM
        required_flow = flow_gpm * self.selection_rules["pump_sizing"]["safety_factor"]
        
        pumps = self.component_db.search_components(
            component_type=ComponentType.PUMP,
            specifications={"flow_rate_gpm": required_flow * 0.8}  # Find pumps with at least 80% of required flow
        )
        
        if not pumps:
            logger.warning("No suitable pumps found")
            return []
        
        # Select the most efficient pump that meets requirements
        selected_pump = max(pumps, key=lambda p: p.specifications.get("efficiency", 0))
        
        # Calculate quantity needed
        pump_capacity = selected_pump.specifications.get("flow_rate_gpm", 0)
        quantity = max(1, int(required_flow / pump_capacity) + 1)  # +1 for redundancy
        
        return [BOMItem(
            component=selected_pump,
            quantity=quantity,
            total_cost=selected_pump.unit_cost * quantity,
            installation_time_hours=8.0 * quantity,
            notes=f"Selected for {flow_gpm:.0f} GPM flow rate"
        )]
    
    def _select_blowers(self, requirements: ProjectRequirements) -> List[BOMItem]:
        """Select blowers for aeration systems"""
        # Estimate air requirement based on flow rate (simplified)
        air_cfm = requirements.flow_rate_mgd * 100  # Rough estimate
        required_cfm = air_cfm * self.selection_rules["blower_sizing"]["safety_factor"]
        
        blowers = self.component_db.search_components(
            component_type=ComponentType.BLOWER,
            specifications={"flow_rate_cfm": required_cfm * 0.8}
        )
        
        if not blowers:
            logger.warning("No suitable blowers found")
            return []
        
        selected_blower = blowers[0]  # Select first suitable blower
        blower_capacity = selected_blower.specifications.get("flow_rate_cfm", 0)
        quantity = max(1, int(required_cfm / blower_capacity) + 1)
        
        return [BOMItem(
            component=selected_blower,
            quantity=quantity,
            total_cost=selected_blower.unit_cost * quantity,
            installation_time_hours=12.0 * quantity,
            notes=f"Selected for {air_cfm:.0f} CFM air requirement"
        )]
    
    def _select_tanks(self, requirements: ProjectRequirements) -> List[BOMItem]:
        """Select tanks based on flow rate and detention time"""
        flow_gpm = requirements.flow_rate_mgd * 694.4
        detention_hours = self.selection_rules["tank_sizing"]["detention_time_hours"]
        required_volume = flow_gpm * 60 * detention_hours  # Convert to gallons
        required_volume *= self.selection_rules["tank_sizing"]["safety_factor"]
        
        tanks = self.component_db.search_components(
            component_type=ComponentType.TANK,
            specifications={"capacity_gal": required_volume * 0.8}
        )
        
        if not tanks:
            logger.warning("No suitable tanks found")
            return []
        
        selected_tank = tanks[0]
        tank_capacity = selected_tank.specifications.get("capacity_gal", 0)
        quantity = max(1, int(required_volume / tank_capacity))
        
        return [BOMItem(
            component=selected_tank,
            quantity=quantity,
            total_cost=selected_tank.unit_cost * quantity,
            installation_time_hours=24.0 * quantity,
            notes=f"Selected for {required_volume:.0f} gallon capacity"
        )]
    
    def _select_membranes(self, requirements: ProjectRequirements) -> List[BOMItem]:
        """Select membrane modules for MBR systems"""
        flow_mgd = requirements.flow_rate_mgd
        flux_rate = self.selection_rules["membrane_sizing"]["flux_rate_gfd"]
        safety_factor = self.selection_rules["membrane_sizing"]["safety_factor"]
        
        # Calculate required membrane area
        required_area = (flow_mgd * 1000000) / flux_rate * safety_factor  # sq ft
        
        membranes = self.component_db.search_components(component_type=ComponentType.MEMBRANE)
        
        if not membranes:
            logger.warning("No suitable membranes found")
            return []
        
        selected_membrane = membranes[0]
        membrane_area = selected_membrane.specifications.get("surface_area_sqft", 0)
        quantity = max(1, int(required_area / membrane_area))
        
        return [BOMItem(
            component=selected_membrane,
            quantity=quantity,
            total_cost=selected_membrane.unit_cost * quantity,
            installation_time_hours=16.0 * quantity,
            notes=f"Selected for {required_area:.0f} sq ft membrane area"
        )]
    
    def optimize_bom(self, bom: BillOfMaterials, optimization_criteria: str = "cost") -> BillOfMaterials:
        """Optimize BOM based on specified criteria"""
        logger.info(f"Optimizing BOM {bom.id} for {optimization_criteria}")
        
        if optimization_criteria == "cost":
            return self._optimize_for_cost(bom)
        elif optimization_criteria == "efficiency":
            return self._optimize_for_efficiency(bom)
        elif optimization_criteria == "environmental":
            return self._optimize_for_environmental_impact(bom)
        else:
            logger.warning(f"Unknown optimization criteria: {optimization_criteria}")
            return bom
    
    def _optimize_for_cost(self, bom: BillOfMaterials) -> BillOfMaterials:
        """Optimize BOM for lowest cost"""
        # Implementation would involve finding alternative components with lower costs
        # For now, return the original BOM
        return bom
    
    def _optimize_for_efficiency(self, bom: BillOfMaterials) -> BillOfMaterials:
        """Optimize BOM for highest efficiency"""
        # Implementation would involve selecting higher efficiency components
        return bom
    
    def _optimize_for_environmental_impact(self, bom: BillOfMaterials) -> BillOfMaterials:
        """Optimize BOM for lowest environmental impact"""
        # Implementation would involve selecting components with better environmental scores
        return bom
    
    async def generate_bom_with_vendor_pricing(self, project_id: str, requirements: ProjectRequirements, 
                                             vendor_client: Optional[VendorClient] = None) -> BillOfMaterials:
        """Generate BOM with live vendor pricing"""
        # Generate base BOM first
        bom = self.generate_bom(project_id, requirements)
        
        if vendor_client:
            # Get component IDs for vendor lookup
            component_ids = [item.component.id for item in bom.items]
            
            try:
                # Get live pricing from vendors
                vendor_components = await vendor_client.get_best_pricing(component_ids)
                
                # Update BOM items with vendor pricing
                vendor_lookup = {comp.model: comp for comp in vendor_components}
                
                updated_items = []
                for item in bom.items:
                    vendor_comp = vendor_lookup.get(item.component.id)
                    if vendor_comp:
                        # Update component with vendor pricing
                        updated_component = item.component.model_copy()
                        updated_component.unit_cost = vendor_comp.unit_price
                        
                        # Update BOM item
                        updated_item = item.model_copy()
                        updated_item.component = updated_component
                        updated_item.total_cost = vendor_comp.unit_price * item.quantity
                        updated_items.append(updated_item)
                    else:
                        updated_items.append(item)
                
                # Recalculate totals
                bom.items = updated_items
                bom.total_material_cost = sum(item.total_cost for item in bom.items)
                bom.total_installation_cost = sum(item.component.installation_cost * item.quantity for item in bom.items)
                bom.total_cost = bom.total_material_cost + bom.total_installation_cost
                
            except Exception as e:
                logger.warning(f"Failed to get vendor pricing, using default prices: {e}")
        
        return bom


# Global instances for backward compatibility
_component_db = ComponentDatabase()
_bom_engine = BOMEngine(_component_db)

def base_bom_for(spec: SystemSpec) -> List[Dict[str, Any]]:
    """Generate base BOM for system specification (backward compatibility function)"""
    # Convert SystemSpec to ProjectRequirements
    requirements = ProjectRequirements(
        flow_rate_mgd=spec.flow_rate_mgd or (spec.capacity_lpd / 3785411.78 if spec.capacity_lpd else 1.0),
        treatment_type=spec.type,
        effluent_standards=spec.treatment_requirements or {},
        site_constraints={"offgrid": spec.offgrid} if hasattr(spec, 'offgrid') else {}
    )
    
    # Generate BOM
    bom = _bom_engine.generate_bom(f"spec_{spec.type}", requirements)
    
    # Convert to simple format expected by cost_model
    bom_items = []
    for item in bom.items:
        bom_items.append({
            "sku": item.component.id,
            "description": f"{item.component.name} ({item.component.manufacturer})",
            "qty": item.quantity,
            "unit_price": item.component.unit_cost
        })
    
    return bom_items

async def base_bom_for_with_vendors(spec: SystemSpec, vendor_client: Optional[VendorClient] = None) -> List[Dict[str, Any]]:
    """Generate base BOM with vendor pricing integration"""
    # Convert SystemSpec to ProjectRequirements
    requirements = ProjectRequirements(
        flow_rate_mgd=spec.flow_rate_mgd or (spec.capacity_lpd / 3785411.78 if spec.capacity_lpd else 1.0),
        treatment_type=spec.type,
        effluent_standards=spec.treatment_requirements or {},
        site_constraints={"offgrid": spec.offgrid} if hasattr(spec, 'offgrid') else {}
    )
    
    # Generate BOM with vendor pricing
    bom = await _bom_engine.generate_bom_with_vendor_pricing(f"spec_{spec.type}", requirements, vendor_client)
    
    # Convert to simple format expected by cost_model
    bom_items = []
    for item in bom.items:
        bom_items.append({
            "sku": item.component.id,
            "description": f"{item.component.name} ({item.component.manufacturer})",
            "qty": item.quantity,
            "unit_price": item.component.unit_cost
        })
    
    return bom_items

def setup_vendor_client() -> VendorClient:
    """Setup and configure vendor client with adapters"""
    from ..vendors.adapters import GrundfosAdapter, GenericDistributorAdapter, MockVendorAdapter
    import os
    
    client = VendorClient()
    
    # Register Grundfos adapter if credentials available
    grundfos_api_key = os.getenv('GRUNDFOS_API_KEY')
    if grundfos_api_key:
        grundfos_creds = VendorCredentials(
            vendor_name="Grundfos",
            base_url="https://api.grundfos.com",
            api_key=grundfos_api_key,
            auth_type="api_key"
        )
        client.register_adapter("grundfos", GrundfosAdapter(grundfos_creds))
    
    # Register generic distributor if credentials available
    distributor_api_key = os.getenv('DISTRIBUTOR_API_KEY')
    if distributor_api_key:
        distributor_creds = VendorCredentials(
            vendor_name="Industrial Supply Co",
            base_url=os.getenv('DISTRIBUTOR_BASE_URL', 'https://api.industrialsupply.com'),
            api_key=distributor_api_key,
            auth_type="api_key"
        )
        client.register_adapter("distributor", GenericDistributorAdapter(distributor_creds))
    
    # Always register mock adapter for development/testing
    mock_creds = VendorCredentials(
        vendor_name="Mock Vendor",
        base_url="http://localhost:8000",
        api_key="mock_key",
        auth_type="api_key"
    )
    client.register_adapter("mock", MockVendorAdapter(mock_creds))
    
    return client
"""
physicell_xml_defaults.py - Studio's canonical defaults for a PhysiCell config (.xml).

The nine fragments below are config/template.xml's non-cell-definition sections, hardcoded
rather than read: template.xml is a config the user can open and save over, so it is not
something to build a new document on. Keep them matching it by hand. They match today
except <initial_conditions>, which is enabled here and disabled there -- callers that do
not want a .csv loaded must turn it off themselves.

XML_DEFAULT_SECTIONS maps a top-level config section name to its *children* as a raw
XML fragment (no wrapper element). SECTION_ORDER is PhysiCell's document order;
<cell_definitions> is inserted after "microenvironment_setup" by whoever assembles a
document, since its content is not a default.

default_phenotype() is the other half: config/template.xml's "default" cell definition,
read once and used to fill in whatever a cell definition arrived without. CELL_DEF_SPEC
says which sections that means.

Authors:
Dr. Daniel Bergman
Rf. Credits.md
"""

import copy
import os
import xml.etree.ElementTree as ET


XML_DEFAULT_SECTIONS = {

    "domain": """
            <x_min>-500</x_min>
            <x_max>500</x_max>
            <y_min>-500</y_min>
            <y_max>500</y_max>
            <z_min>-10</z_min>
            <z_max>10</z_max>
            <dx>20</dx>
            <dy>20</dy>
            <dz>20</dz>
            <use_2D>true</use_2D>
    """,

    "overall": """
            <max_time units="min">7200</max_time>
            <time_units>min</time_units>
            <space_units>micron</space_units>
            <dt_diffusion units="min">0.01</dt_diffusion>
            <dt_mechanics units="min">0.1</dt_mechanics>
            <dt_phenotype units="min">6</dt_phenotype>
    """,

    "parallel": """
            <omp_num_threads>4</omp_num_threads>
    """,

    "save":
      """
            <folder>output</folder>
            <full_data>
                <interval units="min">60</interval>
                <enable>true</enable>
            </full_data>
            <SVG>
                <interval units="min">60</interval>
                <enable>true</enable>
                <plot_substrate enabled="false" limits="false">
                    <substrate>substrate</substrate>
                    <min_conc />
                    <max_conc />
                </plot_substrate>
            </SVG>
            <legacy_data>
                <enable>false</enable>
            </legacy_data>
    """,

    "options": """
            <legacy_random_points_on_sphere_in_divide>false</legacy_random_points_on_sphere_in_divide>
            <virtual_wall_at_domain_edge>true</virtual_wall_at_domain_edge>
            <disable_automated_spring_adhesions>false</disable_automated_spring_adhesions>
            <random_seed>0</random_seed>
        """,
        
    "microenvironment_setup":"""
            <variable name="substrate" units="dimensionless" ID="0">
                <physical_parameter_set>
                    <diffusion_coefficient units="micron^2/min">100000.0</diffusion_coefficient>
                    <decay_rate units="1/min">10</decay_rate>
                </physical_parameter_set>
                <initial_condition units="mmHg">0</initial_condition>
                <Dirichlet_boundary_condition units="mmHg" enabled="False">0</Dirichlet_boundary_condition>
                <Dirichlet_options>
                    <boundary_value ID="xmin" enabled="False">0</boundary_value>
                    <boundary_value ID="xmax" enabled="False">0</boundary_value>
                    <boundary_value ID="ymin" enabled="False">0</boundary_value>
                    <boundary_value ID="ymax" enabled="False">0</boundary_value>
                    <boundary_value ID="zmin" enabled="False">0</boundary_value>
                    <boundary_value ID="zmax" enabled="False">0</boundary_value>
                </Dirichlet_options>
            </variable>
            <options>
                <calculate_gradients>true</calculate_gradients>
                <track_internalized_substrates_in_each_agent>true</track_internalized_substrates_in_each_agent>
                <initial_condition type="matlab" enabled="false">
                    <filename>./config/initial.mat</filename>
                </initial_condition>
                <dirichlet_nodes type="matlab" enabled="false">
                    <filename>./config/dirichlet.mat</filename>
                </dirichlet_nodes>
            </options>
        """,

    "initial_conditions": """
            <cell_positions type="csv" enabled="true">
                <folder>./config</folder>
                <filename>cells.csv</filename>
            </cell_positions>
    """,

    "cell_rules": """
            <rulesets>
                <ruleset protocol="CBHG" version="3.0" format="csv" enabled="false">
                    <folder>./config</folder>
                    <filename>rules0.csv</filename>
                </ruleset>
            </rulesets>
            <settings />
    """,

    "user_parameters": """
            <number_of_cells type="int" units="none" description="initial number of cells (for each cell type)">5</number_of_cells>
    """
}


SECTION_ORDER = tuple(XML_DEFAULT_SECTIONS.keys())

# Where <cell_definitions> belongs relative to SECTION_ORDER. PhysiCell finds sections by
# name so order is cosmetic to the simulator, but Studio's own configs put it here and a
# diff against them should be about content, not layout.
CELL_DEFINITIONS_AFTER = "microenvironment_setup"




# ---------------------------------------------------------------------------
# What a <cell_definition> must contain
# ---------------------------------------------------------------------------

# populate_tree_cell_defs.validate_cell_defs() requires these and sys.exit(-1)s when one
# is absent (unless skip_validate); handle_parse_error() -> sys.exit(-1) is the except
# handler for most of them. A cell_definition missing one does not merely fail to load,
# it takes Studio down.
REQUIRED_PHENOTYPE_SECTIONS = ("cycle", "death", "volume", "mechanics", "motility", "secretion")

# The rest of what Studio's own configs always carry. Not required by validate_cell_defs(),
# but populate_tree_cell_defs() falls back to hardcoded values when they are absent, which
# silently discards whatever the source XML meant to say.
OPTIONAL_PHENOTYPE_SECTIONS = ("cell_interactions", "cell_transformations", "cell_integrity")

# Spec consumed by xml_validate.validate()/fill_missing(). Order is the order sections are
# written back, so a filled-in section lands where Studio would have put it.
CELL_DEF_SPEC = tuple(
    {"path": "phenotype/" + name, "required": name in REQUIRED_PHENOTYPE_SECTIONS}
    for name in REQUIRED_PHENOTYPE_SECTIONS + OPTIONAL_PHENOTYPE_SECTIONS
) + (
    # populate_tree_cell_defs() reads apoptosis one way or the other and sys.exit(-1)s if
    # it finds neither. Carries a predicate, so xml_validate reports it but cannot fill it;
    # filling "phenotype/death" above brings a complete model and clears this too.
    {
        "path": "phenotype/death/model[@name='apoptosis']",
        "required": True,
        "any_of": ("phase_durations", "phase_transition_rates"),
    },
)


# ---------------------------------------------------------------------------
# Default <phenotype>, read from the config Studio ships
# ---------------------------------------------------------------------------

# Last resort if template.xml is missing or unparseable. This is a copy of that file's
# "default" phenotype rather than a shorter stand-in, because "complete" here means every
# field, not every section: populate_tree_cell_defs reads most of them without checking they
# are there, so an empty <volume/> is not a repair, it is a sys.exit(-1) on the next load.
#
# Nothing compares this against config/template.xml. When that file's default cell
# definition gains a field, add it here by hand or the fallback silently drops it.
_FALLBACK_PHENOTYPE = """
    <phenotype>
        <cycle code="6" name="Flow cytometry model (separated)">
            <phase_durations units="min">
                <duration index="0" fixed_duration="false">300.</duration>
                <duration index="1" fixed_duration="true">480.</duration>
                <duration index="2" fixed_duration="true">240.</duration>
                <duration index="3" fixed_duration="true">60.</duration>
            </phase_durations>
        </cycle>
        <death>
            <model code="100" name="apoptosis">
                <death_rate units="1/min">5.31667e-05</death_rate>
                <phase_durations units="min">
                    <duration index="0" fixed_duration="true">516</duration>
                </phase_durations>
                <parameters>
                    <unlysed_fluid_change_rate units="1/min">0.05</unlysed_fluid_change_rate>
                    <lysed_fluid_change_rate units="1/min">0</lysed_fluid_change_rate>
                    <cytoplasmic_biomass_change_rate units="1/min">1.66667e-02</cytoplasmic_biomass_change_rate>
                    <nuclear_biomass_change_rate units="1/min">5.83333e-03</nuclear_biomass_change_rate>
                    <calcification_rate units="1/min">0</calcification_rate>
                    <relative_rupture_volume units="dimensionless">2.0</relative_rupture_volume>
                </parameters>
            </model>
            <model code="101" name="necrosis">
                <death_rate units="1/min">0.0</death_rate>
                <phase_durations units="min">
                    <duration index="0" fixed_duration="true">0</duration>
                    <duration index="1" fixed_duration="true">86400</duration>
                </phase_durations>
                <parameters>
                    <unlysed_fluid_change_rate units="1/min">1.11667e-2</unlysed_fluid_change_rate>
                    <lysed_fluid_change_rate units="1/min">8.33333e-4</lysed_fluid_change_rate>
                    <cytoplasmic_biomass_change_rate units="1/min">5.33333e-5</cytoplasmic_biomass_change_rate>
                    <nuclear_biomass_change_rate units="1/min">2.16667e-3</nuclear_biomass_change_rate>
                    <calcification_rate units="1/min">0</calcification_rate>
                    <relative_rupture_volume units="dimensionless">2.0</relative_rupture_volume>
                </parameters>
            </model>
        </death>
        <volume>
            <total units="micron^3">2494</total>
            <fluid_fraction units="dimensionless">0.75</fluid_fraction>
            <nuclear units="micron^3">540</nuclear>
            <fluid_change_rate units="1/min">0.05</fluid_change_rate>
            <cytoplasmic_biomass_change_rate units="1/min">0.0045</cytoplasmic_biomass_change_rate>
            <nuclear_biomass_change_rate units="1/min">0.0055</nuclear_biomass_change_rate>
            <calcified_fraction units="dimensionless">0</calcified_fraction>
            <calcification_rate units="1/min">0</calcification_rate>
            <relative_rupture_volume units="dimensionless">2.0</relative_rupture_volume>
        </volume>
        <mechanics>
            <cell_cell_adhesion_strength units="micron/min">0.4</cell_cell_adhesion_strength>
            <cell_cell_repulsion_strength units="micron/min">10.0</cell_cell_repulsion_strength>
            <relative_maximum_adhesion_distance units="dimensionless">1.25</relative_maximum_adhesion_distance>
            <cell_adhesion_affinities>
                <cell_adhesion_affinity name="default">1</cell_adhesion_affinity>
            </cell_adhesion_affinities>
            <options>
                <set_relative_equilibrium_distance enabled="false" units="dimensionless">1.8</set_relative_equilibrium_distance>
                <set_absolute_equilibrium_distance enabled="false" units="micron">15.12</set_absolute_equilibrium_distance>
            </options>
            <attachment_elastic_constant units="1/min">0.01</attachment_elastic_constant>
            <attachment_rate units="1/min">0.0</attachment_rate>
            <detachment_rate units="1/min">0.0</detachment_rate>
            <maximum_number_of_attachments>12</maximum_number_of_attachments>
        </mechanics>
        <motility>
            <speed units="micron/min">1</speed>
            <persistence_time units="min">5</persistence_time>
            <migration_bias units="dimensionless">.5</migration_bias>
            <options>
                <enabled>false</enabled>
                <use_2D>true</use_2D>
                <chemotaxis>
                    <enabled>false</enabled>
                    <substrate>substrate</substrate>
                    <direction>1</direction>
                </chemotaxis>
                <advanced_chemotaxis>
                    <enabled>false</enabled>
                    <normalize_each_gradient>false</normalize_each_gradient>
                    <chemotactic_sensitivities>
                        <chemotactic_sensitivity substrate="substrate">0.0</chemotactic_sensitivity>
                    </chemotactic_sensitivities>
                </advanced_chemotaxis>
            </options>
        </motility>
        <secretion>
            <substrate name="substrate">
                <secretion_rate units="1/min">0</secretion_rate>
                <secretion_target units="substrate density">1</secretion_target>
                <uptake_rate units="1/min">0</uptake_rate>
                <net_export_rate units="total substrate/min">0</net_export_rate>
            </substrate>
        </secretion>
        <cell_interactions>
            <apoptotic_phagocytosis_rate units="1/min">0.0</apoptotic_phagocytosis_rate>
            <necrotic_phagocytosis_rate units="1/min">0.0</necrotic_phagocytosis_rate>
            <other_dead_phagocytosis_rate units="1/min">0.0</other_dead_phagocytosis_rate>
            <live_phagocytosis_rates>
                <phagocytosis_rate name="default" units="1/min">0</phagocytosis_rate>
            </live_phagocytosis_rates>
            <attack_rates>
                <attack_rate name="default" units="1/min">0</attack_rate>
            </attack_rates>
            <attack_damage_rate units="1/min">1</attack_damage_rate>
            <attack_duration units="min">0.1</attack_duration>
            <fusion_rates>
                <fusion_rate name="default" units="1/min">0</fusion_rate>
            </fusion_rates>
        </cell_interactions>
        <cell_transformations>
            <transformation_rates>
                <transformation_rate name="default" units="1/min">0</transformation_rate>
            </transformation_rates>
        </cell_transformations>
        <cell_integrity>
            <damage_rate units="1/min">0.0</damage_rate>
            <damage_repair_rate units="1/min">0.0</damage_repair_rate>
        </cell_integrity>
    </phenotype>
"""

_default_phenotype_cache = {}


def default_phenotype(nanohub_flag=False, data_dir=None):
    """A deep copy of the <phenotype> from template.xml's "default" cell definition.

    The source for filling in sections a cell definition arrived without, so it has to be
    complete field by field, not merely section by section; _FALLBACK_PHENOTYPE stands in
    when template.xml is missing or unparseable.
    """
    key = (bool(nanohub_flag), data_dir)
    if key in _default_phenotype_cache:
        return copy.deepcopy(_default_phenotype_cache[key])

    if data_dir:
        path = os.path.join(data_dir, "template.xml")
    else:
        # Mirrors studio.py's split: nanoHUB reads from data/, everyone else from config/.
        path = os.path.join("data" if nanohub_flag else "config", "template.xml")

    pheno = None
    try:
        root = ET.parse(path).getroot()
        for cell_def in root.findall(".//cell_definitions/cell_definition"):
            if cell_def.attrib.get("name") == "default":
                pheno = cell_def.find("phenotype")
                break
        if pheno is None:  # no "default" in this template; any complete one will do
            first = root.find(".//cell_definitions/cell_definition/phenotype")
            pheno = first
    except (OSError, ET.ParseError):
        pheno = None

    if pheno is None:
        pheno = ET.fromstring(_FALLBACK_PHENOTYPE)

    _default_phenotype_cache[key] = pheno
    return copy.deepcopy(pheno)

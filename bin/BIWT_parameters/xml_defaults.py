"""
xml_defaults.py - config defaults for the deprecated in-tree BIWT tab (bin/biwt_tab.py).

The sections themselves now live in bin/physicell_xml_defaults.py, which the current BIWT
bridge uses. This module only rebuilds the dict in the shape biwt_tab.add_xml_defaults()
expects: the same ten keys in the same order, with "cell_definitions" between
"microenvironment_setup" and "initial_conditions". add_xml_defaults() iterates .items() and
appends each in turn, so the order here is the order of the file it writes.

Nothing new should import this. When the deprecated tab goes, so does bin/BIWT_parameters/.
"""

from physicell_xml_defaults import XML_DEFAULT_SECTIONS, CELL_DEFINITIONS_AFTER


# The <cell_definition name="default"> the deprecated tab appends to the file it writes.
# Verbatim, so that tab's output is unchanged. It carries Cortex_1/Dentate_gyrus/...
# asymmetric-division probabilities baked in from one mouse-brain dataset, which is why it
# sits here rather than with the sections every config shares: deleting this directory has
# to delete it too.
LEGACY_DEFAULT_CELL_DEFINITION = """
        <cell_definition name="default" ID="0">
                <phenotype>
                    <cycle code="6" name="Flow cytometry model (separated)">
                        <phase_durations units="min">
                            <duration index="0" fixed_duration="false">300</duration>
                            <duration index="1" fixed_duration="true">480</duration>
                            <duration index="2" fixed_duration="true">240</duration>
                            <duration index="3" fixed_duration="true">60</duration>
                        </phase_durations>
                        <standard_asymmetric_division enabled="False">
                            <asymmetric_division_probability name="default" units="dimensionless">1.0</asymmetric_division_probability>
                            <asymmetric_division_probability name="Cortex_1" units="dimensionless">0</asymmetric_division_probability>
                            <asymmetric_division_probability name="Cortex_2" units="dimensionless">0</asymmetric_division_probability>
                            <asymmetric_division_probability name="Cortex_3" units="dimensionless">0</asymmetric_division_probability>
                            <asymmetric_division_probability name="Cortex_4" units="dimensionless">0</asymmetric_division_probability>
                            <asymmetric_division_probability name="Dentate_gyrus" units="dimensionless">0</asymmetric_division_probability>
                            <asymmetric_division_probability name="Fiber_tracts" units="dimensionless">0</asymmetric_division_probability>
                            <asymmetric_division_probability name="Hippocampus" units="dimensionless">0</asymmetric_division_probability>
                            <asymmetric_division_probability name="Hypothalamus_1" units="dimensionless">0</asymmetric_division_probability>
                            <asymmetric_division_probability name="Lateral_ventricle" units="dimensionless">0</asymmetric_division_probability>
                            <asymmetric_division_probability name="Striatum" units="dimensionless">0</asymmetric_division_probability>
                            <asymmetric_division_probability name="Thalamus_1" units="dimensionless">0</asymmetric_division_probability>
                        </standard_asymmetric_division>
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
                            <cell_adhesion_affinity name="Cortex_1">1.0</cell_adhesion_affinity>
                            <cell_adhesion_affinity name="Cortex_2">1.0</cell_adhesion_affinity>
                            <cell_adhesion_affinity name="Cortex_3">1.0</cell_adhesion_affinity>
                            <cell_adhesion_affinity name="Cortex_4">1.0</cell_adhesion_affinity>
                            <cell_adhesion_affinity name="Dentate_gyrus">1.0</cell_adhesion_affinity>
                            <cell_adhesion_affinity name="Fiber_tracts">1.0</cell_adhesion_affinity>
                            <cell_adhesion_affinity name="Hippocampus">1.0</cell_adhesion_affinity>
                            <cell_adhesion_affinity name="Hypothalamus_1">1.0</cell_adhesion_affinity>
                            <cell_adhesion_affinity name="Lateral_ventricle">1.0</cell_adhesion_affinity>
                            <cell_adhesion_affinity name="Striatum">1.0</cell_adhesion_affinity>
                            <cell_adhesion_affinity name="Thalamus_1">1.0</cell_adhesion_affinity>
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
                        <persistence_time units="min">1</persistence_time>
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
                            <phagocytosis_rate name="Cortex_1" units="1/min">0.0</phagocytosis_rate>
                            <phagocytosis_rate name="Cortex_2" units="1/min">0.0</phagocytosis_rate>
                            <phagocytosis_rate name="Cortex_3" units="1/min">0.0</phagocytosis_rate>
                            <phagocytosis_rate name="Cortex_4" units="1/min">0.0</phagocytosis_rate>
                            <phagocytosis_rate name="Dentate_gyrus" units="1/min">0.0</phagocytosis_rate>
                            <phagocytosis_rate name="Fiber_tracts" units="1/min">0.0</phagocytosis_rate>
                            <phagocytosis_rate name="Hippocampus" units="1/min">0.0</phagocytosis_rate>
                            <phagocytosis_rate name="Hypothalamus_1" units="1/min">0.0</phagocytosis_rate>
                            <phagocytosis_rate name="Lateral_ventricle" units="1/min">0.0</phagocytosis_rate>
                            <phagocytosis_rate name="Striatum" units="1/min">0.0</phagocytosis_rate>
                            <phagocytosis_rate name="Thalamus_1" units="1/min">0.0</phagocytosis_rate>
                        </live_phagocytosis_rates>
                        <attack_rates>
                            <attack_rate name="default" units="1/min">0</attack_rate>
                            <attack_rate name="Cortex_1" units="1/min">0.0</attack_rate>
                            <attack_rate name="Cortex_2" units="1/min">0.0</attack_rate>
                            <attack_rate name="Cortex_3" units="1/min">0.0</attack_rate>
                            <attack_rate name="Cortex_4" units="1/min">0.0</attack_rate>
                            <attack_rate name="Dentate_gyrus" units="1/min">0.0</attack_rate>
                            <attack_rate name="Fiber_tracts" units="1/min">0.0</attack_rate>
                            <attack_rate name="Hippocampus" units="1/min">0.0</attack_rate>
                            <attack_rate name="Hypothalamus_1" units="1/min">0.0</attack_rate>
                            <attack_rate name="Lateral_ventricle" units="1/min">0.0</attack_rate>
                            <attack_rate name="Striatum" units="1/min">0.0</attack_rate>
                            <attack_rate name="Thalamus_1" units="1/min">0.0</attack_rate>
                        </attack_rates>
                        <attack_damage_rate units="1/min">1</attack_damage_rate>
                        <attack_duration units="min">0.1</attack_duration>
                        <fusion_rates>
                            <fusion_rate name="default" units="1/min">0</fusion_rate>
                            <fusion_rate name="Cortex_1" units="1/min">0.0</fusion_rate>
                            <fusion_rate name="Cortex_2" units="1/min">0.0</fusion_rate>
                            <fusion_rate name="Cortex_3" units="1/min">0.0</fusion_rate>
                            <fusion_rate name="Cortex_4" units="1/min">0.0</fusion_rate>
                            <fusion_rate name="Dentate_gyrus" units="1/min">0.0</fusion_rate>
                            <fusion_rate name="Fiber_tracts" units="1/min">0.0</fusion_rate>
                            <fusion_rate name="Hippocampus" units="1/min">0.0</fusion_rate>
                            <fusion_rate name="Hypothalamus_1" units="1/min">0.0</fusion_rate>
                            <fusion_rate name="Lateral_ventricle" units="1/min">0.0</fusion_rate>
                            <fusion_rate name="Striatum" units="1/min">0.0</fusion_rate>
                            <fusion_rate name="Thalamus_1" units="1/min">0.0</fusion_rate>
                        </fusion_rates>
                    </cell_interactions>
                    <cell_transformations>
                        <transformation_rates>
                            <transformation_rate name="default" units="1/min">0</transformation_rate>
                            <transformation_rate name="Cortex_1" units="1/min">0.0</transformation_rate>
                            <transformation_rate name="Cortex_2" units="1/min">0.0</transformation_rate>
                            <transformation_rate name="Cortex_3" units="1/min">0.0</transformation_rate>
                            <transformation_rate name="Cortex_4" units="1/min">0.0</transformation_rate>
                            <transformation_rate name="Dentate_gyrus" units="1/min">0.0</transformation_rate>
                            <transformation_rate name="Fiber_tracts" units="1/min">0.0</transformation_rate>
                            <transformation_rate name="Hippocampus" units="1/min">0.0</transformation_rate>
                            <transformation_rate name="Hypothalamus_1" units="1/min">0.0</transformation_rate>
                            <transformation_rate name="Lateral_ventricle" units="1/min">0.0</transformation_rate>
                            <transformation_rate name="Striatum" units="1/min">0.0</transformation_rate>
                            <transformation_rate name="Thalamus_1" units="1/min">0.0</transformation_rate>
                        </transformation_rates>
                    </cell_transformations>
                    <cell_integrity>
                        <damage_rate units="1/min">0.0</damage_rate>
                        <damage_repair_rate units="1/min">0.0</damage_repair_rate>
                    </cell_integrity>
                </phenotype>
                <custom_data>
                    <sample conserved="false" units="dimensionless" description="">1.0</sample>
                </custom_data>
                <initial_parameter_distributions enabled="false">
                    <distribution enabled="false" type="Uniform" check_base="false">
                        <behavior>substrate secretion target</behavior>
                        <min>0.01</min>
                        <max>0.99</max>
                    </distribution>
                    <distribution enabled="false" type="Normal" check_base="false">
                        <behavior>substrate uptake</behavior>
                        <mu>0.005</mu>
                        <sigma>0.0005</sigma>
                        <lower_bound>0</lower_bound>
                    </distribution>
                    <distribution enabled="false" type="LogNormal" check_base="false">
                        <behavior>substrate secretion</behavior>
                        <mu>2</mu>
                        <sigma>1</sigma>
                        <lower_bound>0.01</lower_bound>
                        <upper_bound>1000</upper_bound>
                    </distribution>
                    <distribution enabled="false" type="LogUniform" check_base="true">
                        <behavior>Volume</behavior>
                        <min>100</min>
                        <max>10000</max>
                    </distribution>
                    <distribution enabled="false" type="Log10Normal" check_base="false">
                        <behavior>custom:sample</behavior>
                        <mu>2</mu>
                        <sigma>2</sigma>
                        <lower_bound>10</lower_bound>
                        <upper_bound>1000</upper_bound>
                    </distribution>
                </initial_parameter_distributions>
            </cell_definition>
        """

xml_defaults = {}
for _key, _fragment in XML_DEFAULT_SECTIONS.items():
    xml_defaults[_key] = _fragment
    if _key == CELL_DEFINITIONS_AFTER:
        xml_defaults["cell_definitions"] = LEGACY_DEFAULT_CELL_DEFINITION
del _key, _fragment

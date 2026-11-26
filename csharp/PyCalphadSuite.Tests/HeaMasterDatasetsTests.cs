using System;
using System.Collections.Generic;
using System.Text.Json;
using PyCalphadSuite.Core.Models;
using Xunit;

namespace PyCalphadSuite.Tests
{
    public class HeaMasterDatasetsTests
    {
        [Fact]
        public void HeaMasterStatisticsDto_DeserializesCorrectly()
        {
            string json = """
            {
                "total_mpea_experimental_records": 1545,
                "total_phase_stability_records": 11252,
                "total_high_temperature_mechanical_records": 668,
                "total_synthesis_process_records": 12427,
                "total_aggregate_records": 25892,
                "alloys_with_yield_strength": 1365,
                "alloys_with_hardness": 900,
                "alloys_with_uts": 539,
                "alloys_with_youngs_modulus": 145,
                "element_coverage_count": 67,
                "unique_elements_modeled": ["Al", "Co", "Cr", "Cu", "Fe", "Mn", "Mo", "Nb", "Ni", "Ta", "Ti", "V", "W", "Zr"]
            }
            """;

            var dto = JsonSerializer.Deserialize<HeaMasterStatisticsDto>(json);
            Assert.NotNull(dto);
            Assert.Equal(25892, dto.TotalAggregateRecords);
            Assert.Equal(1545, dto.TotalMpeaExperimentalRecords);
            Assert.Equal(11252, dto.TotalPhaseStabilityRecords);
            Assert.Equal(1365, dto.AlloysWithYieldStrength);
            Assert.Equal(900, dto.AlloysWithHardness);
            Assert.Equal(67, dto.ElementCoverageCount);
            Assert.Equal(14, dto.UniqueElementsModeled.Count);
        }

        [Fact]
        public void HeaRecordDto_DeserializesMechanicalAndPhaseData()
        {
            string json = """
            {
                "source": "Citrine Informatics MPEA Database",
                "formula": "Al1 Co1 Cr1 Fe1 Ni1",
                "elements": ["Al", "Co", "Cr", "Fe", "Ni"],
                "phase_structure": "BCC+FCC",
                "microstructure": "Dendritic with fine spinodal",
                "processing_method": "CAST",
                "yield_strength_mpa": 1251.0,
                "uts_mpa": 1450.0,
                "hardness_hv": 490.0,
                "elongation_pct": 5.2,
                "youngs_modulus_gpa": 195.0,
                "density_exp_g_cm3": 7.02,
                "test_temperature_c": 25.0
            }
            """;

            var rec = JsonSerializer.Deserialize<HeaRecordDto>(json);
            Assert.NotNull(rec);
            Assert.Equal("Al1 Co1 Cr1 Fe1 Ni1", rec.Formula);
            Assert.Equal(1251.0, rec.YieldStrengthMpa);
            Assert.Equal(490.0, rec.HardnessHv);
            Assert.Equal("CAST", rec.ProcessingMethod);
            Assert.Equal(5, rec.Elements.Count);
        }

        [Fact]
        public void HeaTemperatureYieldCurveDto_DeserializesPoints()
        {
            string json = """
            {
                "formula": "Al0.25NbTaTiZr",
                "count": 2,
                "data_points": [
                    {
                        "temperature_c": 25.0,
                        "temperature_k": 298.15,
                        "yield_strength_mpa": 1745.0,
                        "condition": "As-cast"
                    },
                    {
                        "temperature_c": 1000.0,
                        "temperature_k": 1273.15,
                        "yield_strength_mpa": 366.0,
                        "condition": "As-cast"
                    }
                ]
            }
            """;

            var curve = JsonSerializer.Deserialize<HeaTemperatureYieldCurveDto>(json);
            Assert.NotNull(curve);
            Assert.Equal("Al0.25NbTaTiZr", curve.Formula);
            Assert.Equal(2, curve.Count);
            Assert.Equal(1745.0, curve.DataPoints[0].YieldStrengthMpa);
            Assert.Equal(366.0, curve.DataPoints[1].YieldStrengthMpa);
        }
    }
}

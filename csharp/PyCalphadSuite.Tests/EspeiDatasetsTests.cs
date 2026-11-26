using System;
using System.Collections.Generic;
using System.Text.Json;
using PyCalphadSuite.Core.Models;
using Xunit;

namespace PyCalphadSuite.Tests
{
    public class EspeiDatasetsTests
    {
        [Fact]
        public void EspeiStatisticsDto_DeserializesCorrectly()
        {
            string json = """
            {
                "total_datasets": 215,
                "total_systems": 34,
                "binary_systems_count": 21,
                "ternary_systems_count": 13,
                "total_references": 71,
                "zpf_dataset_count": 94,
                "thermochemical_dataset_count": 121,
                "unique_phases_count": 35,
                "systems": ["Al-Co", "Al-Ni", "Co-Cr-Ni"]
            }
            """;

            var dto = JsonSerializer.Deserialize<EspeiStatisticsDto>(json);
            Assert.NotNull(dto);
            Assert.Equal(215, dto.TotalDatasets);
            Assert.Equal(34, dto.TotalSystems);
            Assert.Equal(21, dto.BinarySystemsCount);
            Assert.Equal(13, dto.TernarySystemsCount);
            Assert.Equal(3, dto.Systems.Count);
        }

        [Fact]
        public void EspeiZpfPointDto_DeserializesCoordinates()
        {
            string json = """
            {
                "system": "Al-Ni",
                "temperature_k": 1645.0,
                "temperature_c": 1371.85,
                "phase": "LIQUID",
                "element": "Ni",
                "composition": 0.755,
                "reference": "ZPF lines",
                "source_file": "AL-NI-ZPF.json"
            }
            """;

            var pt = JsonSerializer.Deserialize<EspeiZpfPointDto>(json);
            Assert.NotNull(pt);
            Assert.Equal("Al-Ni", pt.System);
            Assert.Equal(1645.0, pt.TemperatureK);
            Assert.Equal("LIQUID", pt.Phase);
            Assert.Equal("Ni", pt.Element);
            Assert.Equal(0.755, pt.Composition);
        }

        [Fact]
        public void EspeiThermochemicalPointDto_DeserializesFormationEnthalpy()
        {
            string json = """
            {
                "system": "Al-Co",
                "property": "HM_FORM",
                "temperature_k": 298.15,
                "phase": "BCC_B2",
                "value_si": -57670.0,
                "unit": "J/mol",
                "reference": "liu2015first",
                "source_file": "AL-CO-HM_FORM-BCC_B2.json"
            }
            """;

            var pt = JsonSerializer.Deserialize<EspeiThermochemicalPointDto>(json);
            Assert.NotNull(pt);
            Assert.Equal("Al-Co", pt.System);
            Assert.Equal("HM_FORM", pt.Property);
            Assert.Equal(-57670.0, pt.ValueSi);
            Assert.Equal("J/mol", pt.Unit);
        }
    }
}

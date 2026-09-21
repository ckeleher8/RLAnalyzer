using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace GatewayApi.Models
{
    public class ActionValueTouchDto
    {
        public int Frame { get; set; }
        public string Player { get; set; } = string.Empty;
        public string Team { get; set; } = string.Empty;
        
        [JsonPropertyName("V_Before")]
        public double V_Before { get; set; }

        [JsonPropertyName("V_After")]
        public double V_After { get; set; }

        [JsonPropertyName("Action_Value")]
        public double Action_Value { get; set; }

        [JsonPropertyName("Is_Goal")]
        public bool Is_Goal { get; set; }

        [JsonPropertyName("Is_Save")]
        public bool Is_Save { get; set; }
    }

    public class PlayerSummaryDto
    {
        public string Name { get; set; } = string.Empty;
        public string Team { get; set; } = string.Empty;
        public int Goals { get; set; }
        public int Saves { get; set; }
        public int Shots { get; set; }
        public double Total_Action_Value { get; set; }
        public double Avg_Action_Value { get; set; }
        public double Total_Wasted_Boost { get; set; }
        public int Pad_Pickups { get; set; }
    }

    public class MatchMetadataDto
    {
        public string Map_Name { get; set; } = string.Empty;
        public int Duration_Seconds { get; set; }
        public int Blue_Score { get; set; }
        public int Orange_Score { get; set; }
        public string Winning_Team { get; set; } = string.Empty;
    }

    public class PythonAnalysisReport
    {
        [JsonPropertyName("Match_ID")]
        public string Match_ID { get; set; } = string.Empty;

        [JsonPropertyName("Metadata")]
        public MatchMetadataDto? Metadata { get; set; }

        [JsonPropertyName("Players")]
        public List<PlayerSummaryDto>? Players { get; set; }

        [JsonPropertyName("Heuristics")]
        public Dictionary<string, object>? Heuristics { get; set; }

        [JsonPropertyName("ML_Action_Values")]
        public List<ActionValueTouchDto>? ML_Action_Values { get; set; }
    }

    public class PythonJobStatusResponse
    {
        [JsonPropertyName("status")]
        public string Status { get; set; } = string.Empty;

        [JsonPropertyName("job_id")]
        public string Job_Id { get; set; } = string.Empty;

        [JsonPropertyName("message")]
        public string? Message { get; set; }

        [JsonPropertyName("report")]
        public PythonAnalysisReport? Report { get; set; }
    }

    public class UploadResponseDto
    {
        public int Id { get; set; }
        public string MatchId { get; set; } = string.Empty;
        public string Status { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
    }

    public class MatchResponseDto
    {
        public int Id { get; set; }
        public string MatchId { get; set; } = string.Empty;
        public string FileName { get; set; } = string.Empty;
        public DateTime UploadedAt { get; set; }
        public string Status { get; set; } = string.Empty;
        public string? ErrorMessage { get; set; }
        public string? MapName { get; set; }
        public int DurationSeconds { get; set; }
        public int BlueScore { get; set; }
        public int OrangeScore { get; set; }
        public string? WinningTeam { get; set; }
        public List<PlayerSummaryDto> Players { get; set; } = new();
        public List<ActionValueTouchDto> Touches { get; set; } = new();
        public Dictionary<string, object>? Heuristics { get; set; }
    }
}
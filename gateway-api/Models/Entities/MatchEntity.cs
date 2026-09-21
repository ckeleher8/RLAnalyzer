using System;
using System.Collections.Generic;

namespace GatewayApi.Models.Entities
{
    public class MatchEntity
    {
        public int Id { get; set; }
        public string MatchId { get; set; } = string.Empty;
        public string FileName { get; set; } = string.Empty;
        public DateTime UploadedAt { get; set; } = DateTime.UtcNow;
        public string Status { get; set; } = "Pending"; // Pending, Processing, Completed, Failed
        public string? ErrorMessage { get; set; }
        public string? MapName { get; set; }
        public int DurationSeconds { get; set; }
        public int BlueScore { get; set; }
        public int OrangeScore { get; set; }
        public string? WinningTeam { get; set; }
        public string? RawReportJson { get; set; }

        public List<PlayerStatEntity> PlayerStats { get; set; } = new();
        public List<TouchEntity> Touches { get; set; } = new();
        public List<HeuristicSummaryEntity> Heuristics { get; set; } = new();
    }
}

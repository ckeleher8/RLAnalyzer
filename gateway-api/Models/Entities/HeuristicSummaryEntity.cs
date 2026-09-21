namespace GatewayApi.Models.Entities
{
    public class HeuristicSummaryEntity
    {
        public int Id { get; set; }
        public int MatchId { get; set; }
        public MatchEntity? Match { get; set; }

        public string PlayerName { get; set; } = string.Empty;
        public string MetricType { get; set; } = string.Empty; // ThirdMan, SupersonicWaste, SmallPadPathing
        public string SummaryJson { get; set; } = string.Empty;
        public int WarningCount { get; set; }
    }
}

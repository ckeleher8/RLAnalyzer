namespace GatewayApi.Models.Entities
{
    public class TouchEntity
    {
        public int Id { get; set; }
        public int MatchId { get; set; }
        public MatchEntity? Match { get; set; }

        public int Frame { get; set; }
        public string PlayerName { get; set; } = string.Empty;
        public string Team { get; set; } = string.Empty;
        public double VBefore { get; set; }
        public double VAfter { get; set; }
        public double ActionValue { get; set; }
        public bool IsGoal { get; set; }
        public bool IsSave { get; set; }
    }
}

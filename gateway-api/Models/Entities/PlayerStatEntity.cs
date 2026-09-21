namespace GatewayApi.Models.Entities
{
    public class PlayerStatEntity
    {
        public int Id { get; set; }
        public int MatchId { get; set; }
        public MatchEntity? Match { get; set; }

        public string PlayerName { get; set; } = string.Empty;
        public string Team { get; set; } = string.Empty; // Blue or Orange
        public int Goals { get; set; }
        public int Saves { get; set; }
        public int Shots { get; set; }
        public double TotalActionValue { get; set; }
        public double AvgActionValue { get; set; }
        public double TotalWastedBoost { get; set; }
        public int PadPickupCount { get; set; }
    }
}

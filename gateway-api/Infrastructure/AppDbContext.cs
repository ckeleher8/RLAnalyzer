using Microsoft.EntityFrameworkCore;
using GatewayApi.Models.Entities;

namespace GatewayApi.Infrastructure
{
    public class AppDbContext : DbContext
    {
        public AppDbContext(DbContextOptions<AppDbContext> options) : base(options)
        {
        }

        public DbSet<MatchEntity> Matches => Set<MatchEntity>();
        public DbSet<PlayerStatEntity> PlayerStats => Set<PlayerStatEntity>();
        public DbSet<TouchEntity> Touches => Set<TouchEntity>();
        public DbSet<HeuristicSummaryEntity> Heuristics => Set<HeuristicSummaryEntity>();

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            modelBuilder.Entity<MatchEntity>(entity =>
            {
                entity.HasKey(m => m.Id);
                entity.HasIndex(m => m.MatchId);
                entity.Property(m => m.Status).HasMaxLength(50);
                entity.Property(m => m.FileName).HasMaxLength(255);
            });

            modelBuilder.Entity<PlayerStatEntity>(entity =>
            {
                entity.HasKey(p => p.Id);
                entity.HasOne(p => p.Match)
                      .WithMany(m => m.PlayerStats)
                      .HasForeignKey(p => p.MatchId)
                      .OnDelete(DeleteBehavior.Cascade);
            });

            modelBuilder.Entity<TouchEntity>(entity =>
            {
                entity.HasKey(t => t.Id);
                entity.HasOne(t => t.Match)
                      .WithMany(m => m.Touches)
                      .HasForeignKey(t => t.MatchId)
                      .OnDelete(DeleteBehavior.Cascade);
                entity.HasIndex(t => new { t.MatchId, t.PlayerName });
            });

            modelBuilder.Entity<HeuristicSummaryEntity>(entity =>
            {
                entity.HasKey(h => h.Id);
                entity.HasOne(h => h.Match)
                      .WithMany(m => m.Heuristics)
                      .HasForeignKey(h => h.MatchId)
                      .OnDelete(DeleteBehavior.Cascade);
            });
        }
    }
}

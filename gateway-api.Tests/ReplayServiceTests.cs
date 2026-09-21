using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using GatewayApi.Contracts;
using GatewayApi.Controllers;
using GatewayApi.Infrastructure;
using GatewayApi.Models;
using GatewayApi.Models.Entities;
using GatewayApi.Services;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Xunit;

namespace GatewayApi.Tests
{
    public class MockMlClient : IMlModelClient
    {
        public Task<PythonAnalysisReport> AnalyzeReplayAsync(Stream fileStream, string fileName)
        {
            return Task.FromResult(new PythonAnalysisReport
            {
                Match_ID = "test-match-123",
                Metadata = new MatchMetadataDto
                {
                    Map_Name = "DFH Stadium",
                    Duration_Seconds = 300,
                    Blue_Score = 3,
                    Orange_Score = 1,
                    Winning_Team = "Blue"
                },
                Players = new List<PlayerSummaryDto>
                {
                    new() { Name = "Squishy", Team = "Blue", Goals = 2, Saves = 1, Total_Action_Value = 1.45 },
                    new() { Name = "Jstn", Team = "Orange", Goals = 1, Saves = 2, Total_Action_Value = 0.85 }
                },
                ML_Action_Values = new List<ActionValueTouchDto>
                {
                    new() { Frame = 100, Player = "Squishy", Team = "Blue", Action_Value = 0.45, Is_Goal = true },
                    new() { Frame = 250, Player = "Jstn", Team = "Orange", Action_Value = -0.22 }
                },
                Heuristics = new Dictionary<string, object>
                {
                    { "Blue_Third_Man", new List<object>() }
                }
            });
        }
    }

    public class ReplayServiceTests
    {
        private AppDbContext CreateInMemoryDb()
        {
            var options = new DbContextOptionsBuilder<AppDbContext>()
                .UseInMemoryDatabase(databaseName: Guid.NewGuid().ToString())
                .Options;
            return new AppDbContext(options);
        }

        private IServiceScopeFactory CreateScopeFactory(AppDbContext db, IMlModelClient mlClient)
        {
            var services = new ServiceCollection();
            services.AddSingleton(db);
            services.AddSingleton(mlClient);
            services.AddSingleton<ILogger<ReplayAnalysisService>>(NullLogger<ReplayAnalysisService>.Instance);
            var provider = services.BuildServiceProvider();
            return provider.GetRequiredService<IServiceScopeFactory>();
        }

        [Fact]
        public async Task UploadReplay_CreatesMatchAndReturnsAccepted()
        {
            // Arrange
            var db = CreateInMemoryDb();
            var mlClient = new MockMlClient();
            var scopeFactory = CreateScopeFactory(db, mlClient);
            var service = new ReplayAnalysisService(db, mlClient, scopeFactory, NullLogger<ReplayAnalysisService>.Instance);
            var controller = new ReplayController(service);

            var content = "dummy binary replay content";
            var bytes = Encoding.UTF8.GetBytes(content);
            var formFile = new FormFile(new MemoryStream(bytes), 0, bytes.Length, "file", "match.replay");

            // Act
            var result = await controller.UploadReplay(formFile);

            // Assert
            var acceptedResult = Assert.IsType<AcceptedAtActionResult>(result);
            var uploadResponse = Assert.IsType<UploadResponseDto>(acceptedResult.Value);
            Assert.Equal("Processing", uploadResponse.Status);
            Assert.True(uploadResponse.Id > 0);
        }

        [Fact]
        public async Task GetMatchStatus_ReturnsCorrectStatus()
        {
            // Arrange
            var db = CreateInMemoryDb();
            var mlClient = new MockMlClient();
            var scopeFactory = CreateScopeFactory(db, mlClient);
            var service = new ReplayAnalysisService(db, mlClient, scopeFactory, NullLogger<ReplayAnalysisService>.Instance);

            var match = new MatchEntity
            {
                MatchId = "guid-123",
                FileName = "game.replay",
                Status = "Completed"
            };
            db.Matches.Add(match);
            await db.SaveChangesAsync();

            // Act
            var status = await service.GetMatchStatusAsync(match.Id);

            // Assert
            Assert.NotNull(status);
            Assert.Equal("Completed", status.Status);
        }

        [Fact]
        public async Task GetMatchById_ReturnsFullDtoWithPlayerStatsAndTouches()
        {
            // Arrange
            var db = CreateInMemoryDb();
            var mlClient = new MockMlClient();
            var scopeFactory = CreateScopeFactory(db, mlClient);
            var service = new ReplayAnalysisService(db, mlClient, scopeFactory, NullLogger<ReplayAnalysisService>.Instance);

            var match = new MatchEntity
            {
                MatchId = "guid-456",
                FileName = "grand_finals.replay",
                Status = "Completed",
                MapName = "Mannfield",
                DurationSeconds = 300,
                BlueScore = 4,
                OrangeScore = 2,
                WinningTeam = "Blue",
                PlayerStats = new List<PlayerStatEntity>
                {
                    new() { PlayerName = "GarrettG", Team = "Blue", Goals = 2, TotalActionValue = 1.2 }
                },
                Touches = new List<TouchEntity>
                {
                    new() { Frame = 150, PlayerName = "GarrettG", Team = "Blue", ActionValue = 0.5, IsGoal = true }
                }
            };
            db.Matches.Add(match);
            await db.SaveChangesAsync();

            // Act
            var response = await service.GetMatchByIdAsync(match.Id);

            // Assert
            Assert.NotNull(response);
            Assert.Equal("Mannfield", response.MapName);
            Assert.Equal(4, response.BlueScore);
            Assert.Single(response.Players);
            Assert.Equal("GarrettG", response.Players[0].Name);
            Assert.Single(response.Touches);
            Assert.True(response.Touches[0].Is_Goal);
        }
    }
}

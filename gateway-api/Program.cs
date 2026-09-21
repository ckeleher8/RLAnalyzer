using System;
using GatewayApi.Contracts;
using GatewayApi.Infrastructure;
using GatewayApi.Services;
using Microsoft.AspNetCore.Builder;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

var builder = WebApplication.CreateBuilder(args);

// 1. Add Logging & Controllers
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

// 2. Database Provider Setup (Configurable: Sqlite for ease of local run or SqlServer)
var dbProvider = builder.Configuration.GetValue<string>("DatabaseProvider") ?? "Sqlite";
var sqlServerConn = builder.Configuration.GetConnectionString("DefaultConnection");
var sqliteConn = builder.Configuration.GetConnectionString("SqliteConnection") ?? "Data Source=rl_analyzer.db";

builder.Services.AddDbContext<AppDbContext>(options =>
{
    if (dbProvider.Equals("SqlServer", StringComparison.OrdinalIgnoreCase) && !string.IsNullOrEmpty(sqlServerConn))
    {
        options.UseSqlServer(sqlServerConn);
    }
    else
    {
        options.UseSqlite(sqliteConn);
    }
});

// 3. Register Typed HTTP Client for Python ML Microservice
var pythonBaseUrl = builder.Configuration.GetValue<string>("PythonMlService:BaseUrl") ?? "http://127.0.0.1:8000";
builder.Services.AddHttpClient<IMlModelClient, PythonMlHttpClient>(client =>
{
    client.BaseAddress = new Uri(pythonBaseUrl.TrimEnd('/') + "/");
    client.Timeout = TimeSpan.FromMinutes(5);
});

// 4. Register Domain Services
builder.Services.AddScoped<IReplayAnalysisService, ReplayAnalysisService>();

// 5. Configure CORS for React UI
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowFrontend", policy =>
    {
        policy.WithOrigins(
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:3000",
                "http://127.0.0.1:3000"
            )
            .AllowAnyHeader()
            .AllowAnyMethod()
            .AllowCredentials();
    });
});

var app = builder.Build();

// 6. Ensure Database Created
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    var logger = scope.ServiceProvider.GetRequiredService<ILogger<Program>>();
    try
    {
        db.Database.EnsureCreated();
        logger.LogInformation("Database initialized successfully ({Provider}).", dbProvider);
    }
    catch (Exception ex)
    {
        logger.LogError(ex, "Database initialization error: {Message}", ex.Message);
    }
}

// 7. Middleware Pipeline
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseCors("AllowFrontend");
app.UseAuthorization();

app.MapControllers();

// Health check endpoint
app.MapGet("/api/health", () => Results.Ok(new 
{ 
    status = "healthy", 
    service = "GatewayApi",
    timestamp = DateTime.UtcNow 
}));

app.Run();
